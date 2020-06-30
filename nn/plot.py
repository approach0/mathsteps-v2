import pickle
import matplotlib.pyplot as plt

def draw_and_save(pkl_path, image_prefix):
    """
    将训练的历史数据画成折线图
    """
    with open(pkl_path, 'rb') as fh:
        history = pickle.load(fh)

        fig = plt.figure()
        plt.plot([avg_loss for avg_loss, test_accuracy in history])
        plt.ylabel('avg loss')
        plt.show()
        fig.savefig(image_prefix + '-avg-loss.png')

        fig = plt.figure()
        plt.plot([test_accuracy for avg_loss, test_accuracy in history])
        plt.ylabel('test metrics')
        plt.show()
        fig.savefig(image_prefix + '-test-metrics.png')

        print(max(history, key=lambda x: x[1]))

draw_and_save('train-hist-policy.pkl', 'plt-policy')
draw_and_save('train-hist-value.pkl', 'plt-value')
