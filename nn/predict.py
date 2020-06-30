import torch
import pickle
import sys
sys.path.append('.')

from nn_policy.train import RNN_model
from nn_policy.train import BoW
from nn_policy.train import batch_tensors
from nn_policy.train import tex2tokens
from nn_policy.train import policy_network_configs, value_network_configs
import torch.nn.functional as F

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class NN_models():
    """
    policy network 和 value netwrok 的包装类
    """
    def __init__(self, policy_nn_path, value_nn_path, bow_path):
        print(f'Loading NN models ({policy_nn_path}, {value_nn_path}, {bow_path})...')

        try:
            with open(bow_path, 'rb') as fh:
                self.bow = pickle.load(fh)
        except Exception as err:
            print(err)
            return

        policy_network, policy_opt, policy_loss_fun = policy_network_configs(self.bow, -1, load_path=policy_nn_path)
        self.policy_network  = policy_network.to(device)
        self.policy_opt      = policy_opt
        self.policy_loss_fun = policy_loss_fun

        value_network, value_opt, value_loss_fun = value_network_configs(self.bow, load_path=value_nn_path)
        self.value_network  = value_network.to(device)
        self.value_opt      = value_opt
        self.value_loss_fun = value_loss_fun

        self.device = device
        print('Model loaded.')


def visualize_alpha(alpha, tex, rule):
    """
    将 attention 向量输出到 HTML 可视化
    """
    tokens = tex2tokens(tex)
    tokens = ['SOS'] + tokens
    alpha = alpha.squeeze(2).squeeze(0).cpu().numpy()
    alpha = [a for a in alpha]

    from render_math import render_attention
    from common_axioms import common_axioms

    axioms = common_axioms()
    axiom = axioms[rule]

    render_attention(tex, tokens, alpha, axiom)


def predict_policy(tex, nn_models, k=3):
    """
    根据输入 TeX 预测化简的 policy.
    """
    bow = nn_models.bow
    policy_network = nn_models.policy_network
    with torch.no_grad():
        # predict prolicy
        tokens = tex2tokens(tex)
        inputs, _, _ = batch_tensors([(tokens, 0, 0)], bow, device)
        policy_logits, alpha = policy_network(inputs)
        logprob = F.log_softmax(policy_logits, dim=1) # [B, max_rule]
        probs = torch.exp(logprob)[0]
        # extract top-K probabilities
        top_vals, top_idx = probs.topk(k)
        rules = top_idx - 1
        rules, rule_probs = rules.cpu().numpy(), top_vals.cpu().numpy()
        return rules, rule_probs, alpha


def predict_value(tex, nn_models):
    """
    根据输入 TeX 预测当前状态剩下的步骤数目.
    """
    bow = nn_models.bow
    value_network = nn_models.value_network
    with torch.no_grad():
        tokens = tex2tokens(tex)
        inputs, _, _ = batch_tensors([(tokens, 0, 0)], bow, device)
        values, alpha = value_network(inputs)
        return values[0].item(), alpha


if __name__ == '__main__':
    nn_models = NN_models('model-policy-nn.pretrain.pt', 'model-value-nn.pretrain.pt', 'bow.pkl')

    with torch.no_grad():
        tex = '12+(3 + 4)^{2} + 0'
        tex = '21\\frac{2}{3}+(+3\\frac{1}{4})-(-\\frac{2}{3})-(+\\frac{1}{4})'
        tex = '\left|-2-\\frac{1}{3}\\right|+\\frac{1}{2}'
        tex = "1+2-3\cdot\div5-6+7+8\cdot\div10\div11"
        tex = '\left|-10^{2}\\right|+[(-4)^{2}-(3+3^{2})\cdot 2]'
        tex = '\\frac{-1}{\\frac{2}{3} \cdot \\frac{7}{10}}'

        with torch.no_grad():
            rules, rule_probs, alpha = predict_policy(tex, nn_models)
            value, _ = predict_value(tex, nn_models)

            print('[predict policy]')
            print(rules)
            print(rule_probs)
            print('[estimate value]', value, '=', round(value))

            visualize_alpha(alpha, tex, rules[0])
