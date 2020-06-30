import sys
sys.path.append('.')

from common_axioms import common_axioms
from test_cases import test_case_from_log, output_steps

import torch
from nn_policy.train import BoW, RNN_model
from nn_policy.predict import NN_models

from mcts import mcts
from generator import random_terms
import transform
import rich

#test_exprs = test_case_from_log('80.full-random.txt')
axioms = common_axioms()

nn_models = NN_models('model-policy-nn.finetune.pt', 'model-value-nn.finetune.pt', 'bow.pkl')

try:
    while True:
        expr, error = random_terms()
        #expr, error = ('9 -(\\frac{1}{2})^{3} \cdot \\frac{2}{9} -\\frac{6}{\\frac{2}{3}}', False)

        if error:
            continue

        rich.print('[yellow] ' + expr)
        narr = transform.tex2narr(expr)
        steps = mcts(narr, axioms, debug=False, n_sample_times=60, n_maxsteps=30, nn_models=nn_models, training=True)

        output_steps(steps)
        #input('Enter to continue')

except KeyboardInterrupt:
    print()
finally:
    print('saving models ...')
    torch.save(nn_models.policy_network, 'model-policy-nn.finetune.pt')
    torch.save(nn_models.value_network, 'model-value-nn.finetune.pt')
