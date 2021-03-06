import mxnet as mx
import argparse
import utils
import acc_conv
import acc_fc
import rank_selection
import collections
import json
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model',  help='the model to speed up')
parser.add_argument('-g', '--gpus', default='0', help='the gpus will be used, e.g "0,1,2,3"')
parser.add_argument('--load-epoch',type=int, default=1, help="load the model on an epoch using the model-prefix")
parser.add_argument('--save-model', type=str, default='new-model', help='output model prefix')
parser.add_argument('--config', default=None, help='specify the config file')
parser.add_argument('--ratio', type=float, default=2, help='speed up ratio')
args = parser.parse_args()

model = utils.load_model(args)
if args.config:
  args.config = json.load(open(args.config, 'r'))
else:
  config = {}
  config['conv_params'] = rank_selection.get_ranksel(model, args.ratio)
  config['fc_params'] = {}
  json.dump(config, open('config-rksel-%.1f.json'%(args.ratio), 'w'), indent=2)
  args.config = config

new_model = model
Args = collections.namedtuple('ConvArgs', 'layer K')
for layer, K in args.config['conv_params'].items():
  arg = Args(layer=layer, K=K)  
  new_model = acc_conv.conv_vh_decomposition(new_model, arg)
for layer, K in args.config['fc_params'].items():
  arg = Args(layer=layer, K=K)  
  new_model = acc_fc.fc_decomposition(new_model, arg)
new_model.save(args.save_model, 1)
