import torch
import torch.nn as nn
from torch import optim
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence, pad_sequence

import sys
sys.path.append('.')

import os
import pickle
import random
import math
import rich

from lark import Lark, UnexpectedInput
lark = Lark.open('../grammar.lark', rel_to=__file__, parser='lalr', debug=False)


class RNN_model(nn.Module):
    def __init__(self, hidden_size, n_volcab, n_outdim, rnn_unit, n_layers, n_directions, method='RNN'):
        """
        RNN 模型初始化

        hidden_size: 统一 latent space 维数
        n_volcab: 词汇量
        n_outdim: 输出维数
        rnn_unit: 选用的 RNN 单元
        n_layers: RNN 层数
        n_directions: RNN 方向个数 (1 or 2)
        method: 选择 RNN 方法

        """
        super(RNN_model, self).__init__()
        self.hidden_size = hidden_size
        self.n_layers = n_layers
        self.n_directions = n_directions
        bidirectional = True if self.n_directions == 2 else False

        self.embedding = nn.Embedding(n_volcab, hidden_size)

        self.rnn = rnn_unit(
            hidden_size,
            hidden_size,
            self.n_layers,
            batch_first=True,
            bidirectional=bidirectional
        )

        self.method = method

        self.tiny_linear = nn.Linear(hidden_size, n_outdim)
        self.small_linear = nn.Linear(hidden_size * n_directions, n_outdim)
        self.large_linear = nn.Linear(n_layers * hidden_size * n_directions, n_outdim)
        self.large_hidden_linear = nn.Linear(n_layers * hidden_size * n_directions, hidden_size)

        self.W_a = nn.Linear(hidden_size * n_directions, hidden_size)
        self.U_a = nn.Linear(hidden_size, hidden_size)
        self.V_a = nn.Linear(hidden_size, 1)

        device = next(self.parameters()).device
        sq_scalar = 1.0 / math.sqrt(self.hidden_size)
        self.sq_scalar = torch.tensor(sq_scalar, device=device)

        self.softmax = nn.Softmax(dim=1)

    def rnn_layers(self, input):
        """
        RNN 层定义
        """
        device = next(self.parameters()).device
        padded = pad_sequence(input, batch_first=True).to(device) # [B, 43]
        emb = self.embedding(padded) # [B, 43, H]

        lengths = [tensor.shape[0] for tensor in input]
        packed = pack_padded_sequence(emb, batch_first=True, lengths=lengths, enforce_sorted=False)

        if isinstance(self.rnn, nn.LSTM):
            outputs, (final_hidden, final_mcell) = self.rnn(packed)
        elif isinstance(self.rnn, nn.GRU):
            outputs, final_hidden = self.rnn(packed)
        else:
            raise Exception('unexpected RNN layer...')

        outputs, lengths = pad_packed_sequence(outputs, batch_first=True)
        # print(final_hidden.shape, output.shape)
        # [n_layers * n_directions, B, H],  [B, 43, n_directions * H]
        return final_hidden, outputs, lengths

    def forward(self, input):
        """
        整体网络定义
        """
        alpha = None
        final_hidden, top_hiddens, lengths = self.rnn_layers(input)

        batch_size = final_hidden.shape[1]
        final_hidden = final_hidden.permute(1, 0, 2).reshape(batch_size, -1)
        # final hidden: [B, n_layers * n_directions * H]

        if self.method == 'RNN':
            logits = self.large_linear(final_hidden) # [B, n_outdim]

        elif self.method == 'RNN-SELF-ATTENTION':
            H = top_hiddens # [B, 43, n_directions * H]
            WH = self.W_a(H) # [B, 43, H]

            align = self.V_a(torch.tanh(WH)) # [B, 43, 1]
            alpha = self.softmax(align) # [B, 43, 1]

            context = torch.mul(alpha, top_hiddens) # [B, 43, n_directions * H]
            context = torch.sum(context, dim=1) # [B, n_directions * H]

            logits = self.small_linear(context) # [B, n_outdim]

        elif self.method == 'RNN-ATTENTION-VANILLA':
            H = top_hiddens # [B, 43, n_directions * H]
            WH = self.W_a(H) # [B, 43, H]

            #hidden_logits = self.large_hidden_linear(final_hidden) # [B, H]
            #US = self.U_a(hidden_logits).unsqueeze(1) # [B, 1, H]

            US = self.large_hidden_linear(final_hidden).unsqueeze(1) # [B, 1, H]

            align = self.V_a(torch.tanh(WH + US)) # [B, 43, 1]
            alpha = self.softmax(align) # [B, 43, 1]

            context = torch.mul(alpha, top_hiddens) # [B, 43, n_directions * H]
            context = torch.sum(context, dim=1) # [B, n_directions * H]

            logits = self.small_linear(context) # [B, n_outdim]

        elif self.method == 'RNN-ATTENTION-SCALED-DOT-PRODUCT':
            device = next(self.parameters()).device
            padded = pad_sequence(input, batch_first=True).to(device) # [B, 43]
            Key = self.embedding(padded) # [B, 43, H]

            Query = self.large_hidden_linear(final_hidden).unsqueeze(1) # [B, 1, H]

            dot_product = torch.bmm(Query, Key.transpose(1, 2)) # [B, 1, 43]

            scaled_dot_prod = torch.mul(self.sq_scalar, dot_product) # [B, 1, 43]
            scaled_dot_prod = scaled_dot_prod.transpose(1, 2) # [B, 43, 1]

            alpha = self.softmax(scaled_dot_prod) # [B, 43, 1]

            Value = Key # [B, 43, H]

            context = torch.bmm(alpha.transpose(1, 2), Value) # [B, 1, H]
            context = context.squeeze(1) # [B, H]

            logits = self.tiny_linear(context) # [B, n_outdim]

        else:
            raise Exception('unexpected NN training method.', self.method)

        return logits, alpha


class CRF_model(nn.Module):
    def __init__(self, n_rules):
        super().__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # include a start tag
        self.START_TAG = 0
        self.n_tags = n_rules + 1

        # transitions[i,j] is P(i|j)
        self.transitions = nn.Parameter(
            torch.randn(self.n_tags, self.n_tags).to(self.device)
        )
        self.transitions.data[self.START_TAG, :] = -10000.

    def log_sum_exp(self, vec):
        max_val = torch.max(vec).view(1, -1)
        return max_val + torch.log(torch.sum(torch.exp(vec - max_val)))

    def log_normalizer(self, feats):
        acc_logprob = torch.full((1, self.n_tags), -10000., device=self.device)
        acc_logprob[0][self.START_TAG] = 0. # 100% probability at START_TAG

        for feat in feats:
            tmp_tensor_arr = [torch.tensor([[-10000.]], device=self.device)]

            for rule in range(self.n_tags - 1):
                emit_logprob = feat[0][rule].view(1, -1)
                trans_logprob = self.transitions[rule + 1].view(1, -1)

                tmp = self.log_sum_exp(acc_logprob + emit_logprob + trans_logprob)
                tmp_tensor_arr.append(tmp)

                #print(acc_logprob.shape)
                #print(emit_logprob.shape)
                #print(trans_logprob.shape)
                #print(tmp.shape)
                #print(0)

            acc_logprob = torch.cat(tmp_tensor_arr).view(1, -1)

        return self.log_sum_exp(acc_logprob)[0]

    def log_cond_prob(self, feats, tags):
        tags = [self.START_TAG] + tags
        acc_logprob = torch.zeros(1, device=self.device)
        for t, feat in enumerate(feats):
            emit_logprob = feat[0][tags[t] - 1]
            trans_logprob = self.transitions[tags[t + 1], tags[t]]
            acc_logprob += emit_logprob + trans_logprob
        return acc_logprob

    def forward(self, feats, tags):
        logprob = self.log_cond_prob(feats, tags)
        Z = self.log_normalizer(feats)
        return -(logprob - Z)


class BoW:
    """
    Bag of Words 类，用于存储词典和词 ID 映射
    """
    def __init__(self):
        self.word2index = {}
        self.index2word = {}
        self.n_words = 0

    def addWord(self, w):
        """
        添加新词
        """
        if w not in self.word2index:
            self.word2index[w] = self.n_words
            self.index2word[self.n_words] = w
            self.n_words += 1

    def __str__(self):
        """
        字典字符串
        """
        return str(self.index2word)

    def __getitem__(self, word):
        """
        字典 lookup
        """
        if word in self.word2index:
            return self.word2index[word]
        else:
            print('[BoW] unknown token: ' + word)
            return self.word2index['EOS']


def each_text_file(path, endat=-1):
    """
    读取目录 path 下的所有 txt 文件路径
    """
    cnt = 0
    for dirname, dirs, files in os.walk(path):
        for f in files:
            if cnt >= endat and endat > 0:
                return
            if f.split('.')[-1] == 'txt':
                cnt += 1
                yield (dirname, f)


def tex2tokens(tex):
    """
    TeX 表达式到 token 数组的转换
    """
    tokens = []
    for t in lark.lex(tex):
        tokstr = str(t)
        if t.type == 'NUMBER':
            if '.' in tokstr:
                tokens.append('FLT')
            else:
                num = int(tokstr)
                if abs(num) > 1:
                    tokens.append('INT')
                else:
                    tokens.append(tokstr)
        else:
            tokens.append(tokstr)
    return tokens


def read_data(path, endat=-1):
    """
    读取步骤-policy数据对
    """
    data = []
    for dirname, filename in each_text_file(path, endat):
        path = dirname + '/' + filename

        n_lines = 0
        with open(path, 'r') as fh:
            for line in fh:
                n_lines += 1

        with open(path, 'r') as fh:
            for n, line in enumerate(fh):
                line = line.rstrip()
                fields = line.split('$')
                tex = fields[0].strip()
                tokens = tex2tokens(tex)
                policy = int(fields[1].strip())
                value = -(n_lines - n - 1)
                data.append((tokens, policy, value))
    return data


def gen_bow(data):
    """
    从数据集生成 Bag-of-Word
    """
    bow = BoW()
    bow.addWord('EOS')
    bow.addWord('SOS')
    for tokens, _, _ in data:
        for tok in tokens:
            bow.addWord(tok)
    return bow


def batch_tensors(data_batch, bow, device):
    """
    将数据 batch 转换成 tensor
    """
    x_batch = [['SOS'] + tokens for tokens, _, _ in data_batch]
    x_batch = [[bow[t] for t in x] for x in x_batch]
    x_batch = [torch.tensor(x) for x in x_batch]

    policy_batch = [policy for _, policy, _ in data_batch]
    policy_batch = torch.tensor(policy_batch).to(device)

    value_batch = [value for _, _, value in data_batch]
    value_batch = torch.tensor(value_batch, dtype=torch.float).to(device)
    return x_batch, policy_batch, value_batch


def batch_generator(data, n_epoch=1, batch_size=64, no_batch=False):
    """
    将数据分成指定 epoch 个数的训练 batch
    """
    if no_batch:
        yield 0, len(data), data
        return

    M = len(data) // batch_size
    for epoch in range(n_epoch):
        idx = 0
        for batch in range(M):
            batch_data = data[idx: idx + batch_size]
            idx += batch_size
            yield epoch, batch, batch_data

        random.shuffle(data)


def sequence_generator(data, n_epoch=10):
    """
    将数据分成指定 epoch 个数的训练 sequence
    """
    for epoch in range(n_epoch):
        seq = []
        for i, d in enumerate(data):
            policy = d[1]
            seq.append(d)
            if policy == 0:
                yield epoch, seq
                seq = []


class TrainingEvaluator:
    """
    训练过程局部统计类
    """
    def __init__(self, eval_interval=200):
        self.acc_loss = 0
        self.eval_cnt = 0
        self.eval_interval = eval_interval

    def tick(self, loss):
        """
        记录一次 loss
        """
        self.acc_loss += loss
        self.eval_cnt += 1
        return self.eval_cnt % self.eval_interval

    def reset(self):
        """
        统计最近的 loss 数据，并重置
        """
        avg_loss = self.acc_loss / self.eval_interval
        self.acc_loss = 0
        self.eval_cnt = 0
        return avg_loss


def policy_network_configs(bow, max_rule, load_path='model-policy-nn.pt'):
    """
    获得 policy network 的配置（模型、优化方法和损失函数）
    如果指定了 load_path，则从对应的路径去读取模型。
    """
    latent_size = 256
    n_rnn_layers = 1
    n_directions = 2
    rnn_unit = nn.GRU
    #rnn_unit = nn.LSTM

    try:
        with open(load_path, 'rb') as fh:
            print('Loading existing policy network', load_path)
            model = torch.load(load_path)
    except Exception as err:
        print(err)
        print('Creating new policy network ...')
        model = RNN_model(
            latent_size, bow.n_words, max_rule + 1, rnn_unit, n_rnn_layers, n_directions,
            #method = 'RNN'
            #method = 'RNN-SELF-ATTENTION'
            method = 'RNN-ATTENTION-VANILLA'
            #method = 'RNN-ATTENTION-SCALED-DOT-PRODUCT'
        )

    #opt = optim.Adam(model.parameters(), lr=0.001)
    opt = optim.AdamW(model.parameters())
    loss_fun = nn.NLLLoss()

    return model, opt, loss_fun


def value_network_configs(bow, load_path='model-value-nn.pt'):
    """
    获得 value network 的配置（模型、优化方法和损失函数）
    如果指定了 load_path，则从对应的路径去读取模型。
    """
    latent_size = 256
    n_rnn_layers = 2
    n_directions = 1
    rnn_unit = nn.GRU
    #rnn_unit = nn.LSTM

    try:
        with open(load_path, 'rb') as fh:
            print('Loading existing value network', load_path)
            model = torch.load(load_path)
    except Exception as err:
        print(err)
        print('Creating new value network ...')
        model = RNN_model(
            latent_size, bow.n_words, 1, rnn_unit, n_rnn_layers, n_directions,
            method = 'RNN'
        )

    #opt = optim.Adam(model.parameters(), lr=0.001)
    opt = optim.AdamW(model.parameters())
    loss_fun = nn.MSELoss()

    return model, opt, loss_fun


def train_crf(train_data, bow):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    #device = 'cpu'
    print('[training on]', device)

    max_rule = max(train_data, key=lambda x: x[1])[1]
    print('[max rule]', max_rule)

    policy_network, policy_opt, policy_loss_fun = policy_network_configs(bow, max_rule, load_path=None)
    policy_network = policy_network.to(device)

    crf_graph = CRF_model(max_rule + 1)
    crf_graph = crf_graph.to(device)
    crf_opt = optim.SGD(crf_graph.parameters(), lr=0.01, weight_decay=1e-4)

    try:
        for n, (epoch, seq) in enumerate(sequence_generator(train_data, n_epoch=10)):
            seq_logits = []
            truth_tags = []
            for step in seq:
                x_batch, p_batch, v_batch = batch_tensors([step], bow, device)

                policy_logits, _ = policy_network(x_batch) # [1, max_rule]
                seq_logits.append(policy_logits)
                truth_tags.append(step[1] + 1)

            policy_opt.zero_grad()
            crf_graph.zero_grad()

            nll = crf_graph(seq_logits, truth_tags)
            print(f'[epoch={epoch}, expr#{n}] loss =', nll.item())
            print()
            nll.backward()

            crf_opt.step()
            policy_opt.step()

    except KeyboardInterrupt:
        print()
    finally:
        print('saving models ...')
        torch.save(policy_network, 'model-policy-nn.crf.pt')
        torch.save(crf_graph, 'model-crf.pt')


def k_fold(data, k=5):
    random.shuffle(data)
    L = len(data)
    fold_sz = L // k
    remain = L - k * fold_sz
    fold_sz = [fold_sz] * k
    for i in range(remain):
        fold_sz[i] += 1
    pos = 0
    for i in range(k):
        a, b = (pos, pos + fold_sz[i])
        test_data = data[a:b]
        train_data = data[:a] + data[b:]
        yield train_data, test_data, i, a, b


def evaluate(policy_network, value_network, test_data, bow, device):
    policy_corrects = 0
    sum_delta_abs = 0
    for epoch, batch, test_batch in batch_generator(test_data, batch_size=1024):
        x_batch, p_batch, v_batch = batch_tensors(test_batch, bow, device)

        # evaluate policy network for this batch
        policy_logits, _ = policy_network(x_batch)
        logprob = F.log_softmax(policy_logits, dim=1) # [B, max_rule]
        top_val, top_idx = logprob.topk(1, dim=1)
        top_val, top_idx = top_val.squeeze(), top_idx.squeeze()
        corrects = torch.sum(top_idx == p_batch).item()
        policy_corrects += corrects

        # evaluate value network for this batch
        value_predicts, _ = value_network(x_batch)
        value_predicts = value_predicts.squeeze(1).round()
        sum_delta_abs += torch.sum(torch.abs(value_predicts - v_batch)).item()

    test_accuracy = policy_corrects / len(test_data)
    print('[policy test accuracy] %.1f%%' % (test_accuracy * 100.))
    value_test_avg_delta = sum_delta_abs / len(test_data)
    print('[value test avg delta] %.2f' % value_test_avg_delta)
    return test_accuracy, value_test_avg_delta


def train_rnn(train_data, test_data, bow):
    """
    训练函数
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    #device = 'cpu'
    print('[training on]', device)

    max_rule = max(train_data, key=lambda x: x[1])[1]
    print('[max rule]', max_rule)

    policy_network, policy_opt, policy_loss_fun = policy_network_configs(bow, max_rule, load_path=None)
    policy_network = policy_network.to(device)

    value_network, value_opt, value_loss_fun = value_network_configs(bow, load_path=None)
    value_network = value_network.to(device)

    policy_network.train()
    value_network.train()

    policy_train_eval = TrainingEvaluator()
    value_train_eval = TrainingEvaluator()

    policy_train_history = []
    value_train_history = []

    try:
        print('[sort by length]')
        train_data.sort(key=lambda x: len(x[0]), reverse=False)

        for epoch, batch, train_batch in batch_generator(train_data, n_epoch=2):
            # batch data to tensors
            x_batch, p_batch, v_batch = batch_tensors(train_batch, bow, device)

            # feed policy network
            policy_logits, _ = policy_network(x_batch)
            logprob = F.log_softmax(policy_logits, dim=1) # [B, max_rule]
            policy_loss = policy_loss_fun(logprob, p_batch)

            policy_opt.zero_grad()
            policy_loss.backward()
            policy_opt.step()

            # feed value network
            value_predicts, _ = value_network(x_batch)
            value_predicts = value_predicts.squeeze(1) # [B]
            value_loss = value_loss_fun(value_predicts, v_batch)

            value_opt.zero_grad()
            value_loss.backward()
            value_opt.step()

            # print on-the-fly evaluation
            policy_train_tick = policy_train_eval.tick(policy_loss.item())
            value_train_tick = value_train_eval.tick(value_loss.item())

            if policy_train_tick == 0 or value_train_tick == 0:

                maxlen = max(map(lambda x: len(x), x_batch))
                minlen = min(map(lambda x: len(x), x_batch))

                policy_avg_loss = policy_train_eval.reset()
                value_avg_loss = value_train_eval.reset()

                print()
                print(f'fold {fold_idx}, epoch {epoch}, batch #{batch}, len: {minlen}, {maxlen}')
                print('[policy avg loss] %.1f' % policy_avg_loss)
                print('[value avg loss] %.1f' % value_avg_loss)

                # on-the-fly test-data evaluation
                policy_test_accuracy, value_test_avg_delta = evaluate(policy_network, value_network, test_data, bow, device)

                policy_train_history.append((policy_avg_loss, policy_test_accuracy))
                value_train_history.append((value_avg_loss, value_test_avg_delta))

    except KeyboardInterrupt:
        print()
    finally:
        with open('train-hist-policy.pkl', 'wb') as fh:
            pickle.dump(policy_train_history, fh)
        with open('train-hist-value.pkl', 'wb') as fh:
            pickle.dump(value_train_history, fh)

        print('saving models ...')
        torch.save(policy_network, 'model-policy-nn.pretrain.pt')
        torch.save(value_network, 'model-value-nn.pretrain.pt')

        rich.print('[red]testdata evaluation of this fold:[/]')
        return evaluate(policy_network, value_network, test_data, bow, device)


if __name__ == '__main__':
    print('[reading data]', end=' ')
    data = []
    for path in ['~/Desktop/output-MCTS-400', '~/Desktop/output-DFS-MCTS-r8000-fr800']:
    #for path in ['~/Desktop/output-MCTS-400']:
        path = path.replace("~", "/home/dm")
        data += read_data(path, endat=-1)
    print(len(data))

    bow = gen_bow(data)

    with open('bow.pkl', 'wb') as fh:
        pickle.dump(bow, fh)

    n_fold = 10
    policy_eval_results = []
    value_eval_results = []
    for train_data, test_data, fold_idx, _, _ in k_fold(data, k=n_fold):
        print()
        rich.print(f'[[test fold #{fold_idx}/#{n_fold}]]', len(train_data), len(test_data))
        policy_test_accuracy, value_test_avg_delta = train_rnn(train_data, test_data, bow)

        policy_eval_results.append(policy_test_accuracy)
        value_eval_results.append(value_test_avg_delta)

    #print(policy_eval_results)
    #print(value_eval_results)
    crossvalid_accuracy = sum(policy_eval_results) / len(policy_eval_results)
    crossvalid_avg_delta = sum(value_eval_results) / len(value_eval_results)
    rich.print('[red]policy cross-evaluation accuracy: %.1f%%[/]' % (crossvalid_accuracy * 100.))
    rich.print('[red]value cross-evaluation delta: %.2f[/]' % crossvalid_avg_delta)

    with open('test-policy-eval-results.pkl', 'wb') as fh:
        pickle.dump(policy_eval_results, fh)
    with open('test-value-eval-results.pkl', 'wb') as fh:
        pickle.dump(value_eval_results, fh)
