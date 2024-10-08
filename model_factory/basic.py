
import torch
import torch.nn as nn

torch.manual_seed(10)

def get_activation_module(name):
    name = name.lower()
    if name == 'relu':
        return nn.ReLU
    elif name == 'tanh':
        return nn.Tanh
    elif name == 'sigmoid':
        return nn.Sigmoid
    else:
        raise Exception("Unknown activation type: {}".format(
            name
        ))

def indent(text, amount, ch=' '):
    padding = ch*amount
    return ''.join(padding + line for line in text.splitlines(True))


def normalize_2d(x, eps=1e-8):
    assert x.dim() == 2
    vl2 = x.norm(2,1)
    return x/((vl2+eps).unsqueeze(1).expand_as(x))

def cosine_similarity(u, v):
    u2 = normalize_2d(u)
    v2 = normalize_2d(v)
    assert u2.dim() == 2
    assert v2.dim() == 2
    return (u2*v2).sum(1)

class ModelBase(nn.Module):

    @staticmethod
    def add_config(cfgparser):
        cfgparser.add_argument("--criterion", type=str, default="classification",
            help="which to use for training"
        )

    def __init__(self, configs):
        super(ModelBase, self).__init__()
        self.criterion = configs.criterion

    def build_output_op(self):
        crt = self.criterion
        if crt == 'classification':
            self.output_op = nn.Linear(self.n_out, 1)
        elif crt == 'classification2':
            self.output_op = nn.Linear(self.n_out, 2)
        elif crt == 'cosine':
            self.output_op = cosine_similarity
        else:
            raise Exception("Unknown criterion: {}".format(crt))

    def compute_similarity(self, left, right):
        crt = self.criterion
        if crt == 'classification':
            self.output_op.weight.data.clamp_(min=1e-6)
            out = left*right
            hidden = self.output_op(out) # (batch, 1)
            return torch.cat((-hidden, hidden), 1)
        elif crt == 'classification2':
            self.output_op.weight[0].data.zero_()
            self.output_op.weight[1].data.clamp_(min=1e-6)
            out = left*right
            return self.output_op(out)
        elif crt == 'cosine':
            return self.output_op(left, right)
        else:
            raise Exception("Unknown criterion: {}".format(crt))

    def compute_loss(self, output, target):
        crt = self.criterion
        if crt == 'classification':
            return nn.functional.cross_entropy(output, target)
        elif crt == 'classification2':
            return nn.functional.cross_entropy(output, target)
        elif crt == 'cosine':
            k = int(target.size(0)/2)
            #print target[0]
            assert target[0] == 1
            assert target[k] == 0
            hinge_loss = (output[k:]+0.25-output[:k]).clamp(min=0.0)
            return hinge_loss.mean()
        else:
            raise Exception("Unknown criterion: {}".format(crt))


