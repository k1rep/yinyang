import argparse
import os

from src.utils import random_string
from src.modules.OptionGenerator import OptionGenerator
from config.config import solvers
from src.modules.exitcodes import *

rootpath = "/".join(__file__.split('/')[:-2])

parser = argparse.ArgumentParser()
parser.add_argument(
    "SOLVER_CLIS",
    help="solvers' command-line interfaces for solving .smt2 files"
)
parser.add_argument(
    "PATH_TO_SEEDS",
    nargs='+',
    help="path to the seed files/folders"
)
parser.add_argument(
    "-s","--strategy",
    choices=["opfuzz", "fusion"],
    default="opfuzz",
    help="sets the mutation strategy (default: opfuzz)."
)
parser.add_argument(
    "-o","--oracle",
    choices=["sat", "unsat"],
    default="unknown",
    help="set oracle for semantic fusion strategy (default: unknown)"
)
parser.add_argument(
    "-i", "--iterations",
    type=int,
    help="the number of iterations on each individual seed. (default: 300 [opfuzz] / 30 [fusion])"
)
parser.add_argument(
    "-m", "--modulo",
    type=int,
    default=2,
    help="specifies how often the mutants will be forwarded to the SMT solvers. For example, with 300 iterations\
          and 2 as a modulo, 150 mutants per seed file will be passed to the SMT solvers. High modulo and iteration\
          counts, prioritize deeper mutations. (default: 2)"
)

parser.add_argument(
    "-logs","--logfolder",
    default=rootpath+"/logs",
    help="set logs folder (default: "+rootpath+"/logs)"
)


parser.add_argument(
    "-t", "--timeout",
    default=8,
    type=int,
    help="imposes a timeout limit (in seconds) on each SMT solver for solving  mutant formula (default: 8)"
)
parser.add_argument(
    "-d", "--diagnose",
    action='store_true',
    help="forwards solver outputs to stdout e.g. for solver command line diagnosis"
)

parser.add_argument(
    "-optfuzz","--optfuzz",
    default="",
    help="read solvers' option setting and enable option fuzzing"
)
parser.add_argument(
    "-name","--name",
    default=random_string(),
    help="set name of this fuzzing instance (default: random string)"
)
parser.add_argument(
    "-bugs","--bugsfolder",
    default=rootpath+"/bugs",
    help="set bug folder (default: "+rootpath+"/bugs)"
)
parser.add_argument(
    "-scratch","--scratchfolder",
    default=rootpath+"/scratch",
    help="specifies where the mutant formulas are temporarily stored.\
         Note, if you run yinyang with several processes in parallel, each\
         instance should have its own scratch folder. (default:"+rootpath+"/scratch)"
)
parser.add_argument(
    "-opconfig","--opconfig",
    default=rootpath+"/config/operator_mutations.txt",
    help="set operator mutation configuration (default: "+rootpath+"/config/operator_mutations.txt)"
)
parser.add_argument(
    "-fusionfun","--fusionfun",
    default=rootpath+"/config/fusion_functions.txt",
    help="set fusion function configuration (default: "+rootpath+"/config/fusion_functions.txt)"
)
parser.add_argument(
    "-km", "--keep-mutants",
    action='store_true',
    help="do not delete the mutants from the scratch folder.\
          Warning: beware that this can quickly exhaust your entire disk space."
)
parser.add_argument(
    "-q", "--quiet",
    action='store_true',
    help="do not output statistics and other output"
)
parser.add_argument(
    "-fl", "--file-size-limit",
    default=100000,
    type=int,
    help="file size limit on seed formula in bytes"
)

args = parser.parse_args()

# pre-processing

# Parse CLI
if args.SOLVER_CLIS == "":
    if len(solvers) == 0:
         print("Error: no solver specified. Either change the commandline or edit solver config file")
         exit(ERR_USAGE)

    args.SOLVER_CLIS = solvers
else: args.SOLVER_CLIS = args.SOLVER_CLIS.split(";") + solvers

if args.timeout <= 0:
    print("Error: timeout should not be a negative number or zero")
    exit(ERR_USAGE)


if not args.iterations:
    if args.strategy == "opfuzz":
        args.iterations = 300
    else:
        args.iterations = 30

if args.iterations <= 0:
    print("Error: iterations should not be a negative number zero")
    exit(ERR_USAGE)

if not os.path.isdir(args.bugsfolder):
    try:
        os.mkdir(args.bugsfolder)
    except Exception as e:
        print("Error: bug folder cannot be created")
        exit(ERR_EXHAUSTED_DISK)


if not os.path.isdir(args.logfolder):
    try:
        os.mkdir(args.logfolder)
    except Exception as e:
        print("Error: log folder cannot be created")
        exit(ERR_EXHAUSTED_DISK)

if not os.path.isdir(args.scratchfolder):
    try:
        os.mkdir(args.scratchfolder)
    except Exception as e:
        print("Error: scratch folder cannot be created")
        exit(ERR_EXHAUSTED_DISK)

temp_seeds = []
for path in args.PATH_TO_SEEDS:
    if not os.path.exists(path):
        print("Error: %s does not exist" % (path))
        exit(ERR_USAGE)
    if os.path.isfile(path):
        temp_seeds.append(path)
    elif os.path.isdir(path):
        for subdir, dirs, files in os.walk(path):
            for filename in files:
                filepath = subdir + os.sep + filename
                if filepath.endswith(".smt2"):
                    temp_seeds.append(filepath)
    else:
        print("Error: %s is neither a file nor a directory")
        exit(ERR_USAGE)

args.PATH_TO_SEEDS = temp_seeds

if (args.strategy == "opfuzz" and len(args.PATH_TO_SEEDS) < 1):
    print("Error: please provide at least one seed for opfuzz strategy.")
    exit(ERR_USAGE)
if (args.strategy == "fusion" and len(args.PATH_TO_SEEDS) < 2):
    print("Error: please provide at least two seeds for fusion strategy.")
    exit(ERR_USAGE)

if args.optfuzz == "": args.optfuzz = None
else: args.optfuzz = OptionGenerator(args.optfuzz)
