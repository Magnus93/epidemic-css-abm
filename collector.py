# collects results from multible simulations 
from simulator import * 
import random 
import math 
import pandas as pd 
import statistics
import time 
from aux_functions import * 
from prob import * 
import matplotlib.pyplot as plt  

class Collector:
    def __init__(self, uncertainty): 
        self.uncertainty = uncertainty 

        # number of susceptibles at start 
        self.NS = 1000

        self.epidemic_limit = 0.1*self.NS 
        self.print_every = 10 
        self.skip_non_epidemics = False

        self.table = pd.DataFrame(columns = ['Duration', 'Epidemic', 'Removed high risk', 'Removed low risk'])
        self.stats = pd.DataFrame(columns = ['Measurement', 'mean', 'Std. Dev', 'Conf. Int (avg)', 'Min', 'Max'])
        self.density = pd.DataFrame(columns = ['Range', 'PDF', 'CDF']) 

        # count the number of replications 
        self.i = 0  
        self.skipped = 0 
        self.below_epidemic_limit = 0 

    def set_skip_non_epidemics(bool_value):
        self.skip_non_epidemics = bool_value  

    def new_sim(self):
        if (self.uncertainty["init"]):
            self.N_high = binomial(self.NS, 0.5) 
        else:
            self.N_high = int(self.NS/2) 
        
        self.N_low = self.NS - self.N_high
        pop_specs = [
            {"amount": self.N_high, "init_stage": "S", "p": 1/5000,  "group_name": "high_risk" }, 
            {"amount": self.N_low, "init_stage": "S", "p": 1/15000, "group_name": "low_risk" }, 
            {"amount": 1, "init_stage": "E"}
        ]
        return Simulator(pop_specs, self.uncertainty)   

    def step(self):
        sim = self.new_sim() 
        sim.run(print_every=False)

        epidemic_size = self.NS - sim.get_num("S")         

        if (self.skip_non_epidemics and epidemic_size < self.epidemic_limit):
            self.skipped += 1 
        else:
            self.i += 1 
            self.table.loc[len(self.table)] = [
                sim.time,
                epidemic_size,  
                self.N_high - sim.get_num("S", "high_risk"),
                self.N_low - sim.get_num("S", "low_risk") 
            ] 
            if (epidemic_size < self.epidemic_limit):
                self.below_epidemic_limit += 1  
            
            if self.i%self.print_every == 0 and self.i != 0:
                time_past = time.time() - self.start_time 
                eta =  time_past*(self.num_reps - self.i) / self.i
                print("iteration {}, \t eta: {}, \t skipped: {}".format(self.i, sec_to_str(eta), self.skipped))


    def run(self, num_reps):
        self.start_time = time.time()
        self.num_reps = num_reps 
        while self.i < self.num_reps:
            self.step()
        
        mean = statistics.mean(self.table['Duration'].tolist()) 
        stdev = statistics.stdev(self.table['Duration'].tolist())
        sterror = stdev / math.sqrt(self.num_reps-1) 
        self.stats.loc[0] = [
            'Duration',
            mean,
            stdev,
            str(mean-sterror)+"  -  "+str(mean+sterror),
            min(self.table['Duration'].tolist()),
            max(self.table['Duration'].tolist()),
        ]

        mean = statistics.mean(self.table['Epidemic'].tolist()) 
        stdev = statistics.stdev(self.table['Epidemic'].tolist())
        sterror = stdev / math.sqrt(self.num_reps-1) 
        self.stats.loc[1] = [
            'Epidemic',
            mean,
            stdev,
            str(mean-sterror)+"  -  "+str(mean+sterror),
            min(self.table['Epidemic'].tolist()),
            max(self.table['Epidemic'].tolist()),
        ]

        bins = 20
        minimum = 0
        maximum = 1000 

        hist = get_hist_pdf(self.table["Epidemic"].tolist(), bins, minimum, maximum)
        self.density["Range"] = hist[1][:bins]
        self.density["PDF"] = hist[0]
        self.density["CDF"] = get_hist_cdf(self.table["Epidemic"].tolist(), bins, minimum, maximum) 

        exec_time = time.time() - self.start_time
        print("####### Collection DONE #######")
        print("Exec. time: \t{}".format(sec_to_str(exec_time)))
        print("num. repl.: \t{}".format(self.i))
        print("Skipped replications: \t{}".format(self.skipped)) 
        print("Replications without epidemics: \t{}".format(self.below_epidemic_limit))
        
        filename = save_pandas_dataframe_as_csv(self.table.sort_values(by="Epidemic"), "abm-table-"+str(self.num_reps))
        print("Table saved as: {}".format(filename))
        filename = save_pandas_dataframe_as_csv(self.stats, "abm-stats-"+str(self.num_reps))
        print("Stats saved as: {}".format(filename))
        filename = save_pandas_dataframe_as_csv(self.density, "abm-density-"+str(self.num_reps)+"reps-"+str(bins)+"bins")
        print("Density saved as: {}".format(filename))

if __name__ == "__main__":
    import sys
    num_reps = 30 
    if len(sys.argv) >= 2:
        num_reps = int(sys.argv[1])

    collector = Collector(uncertainty={ "init":False, "param": False, "auth": False}) 
    collector.run(num_reps)