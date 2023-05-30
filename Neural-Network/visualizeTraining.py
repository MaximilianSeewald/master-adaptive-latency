import time

from tensorboard import program

tracking_address = "./savedLSTMCNNModel/logs/"
#tracking_address = "./savedDenseModel/logs/"
#tracking_address = "./savedLSTMModel/logs/"

if __name__ == "__main__":
    tb = program.TensorBoard()
    tb.configure(argv=[None, '--logdir', tracking_address])
    tb.main()