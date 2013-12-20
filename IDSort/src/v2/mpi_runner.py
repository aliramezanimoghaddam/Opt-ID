# Run this script with a suitable mpirun command. 
# The DLS controls installation of h5py is built against openmpi version 1.6.5.
# Note that the current default mpirun in the controls environment (module load controls-tools)
# is an older version of mpirun - so use the full path to mpirun as demonstrated in the
# example below.
#
# For documentation, see: http://www.h5py.org/docs/topics/mpi.html
# 
# Example:
# /dls_sw/prod/tools/RHEL6-x86_64/openmpi/1-6-5/prefix/bin/mpirun -np 5 dls-python parallel-hdf5-demo.py
#

# First to pick up the DLS controls environment and versioned libraries
from pkg_resources import require
require('mpi4py==1.3.1')
require('h5py==2.2.0')
require('numpy') # h5py need to be able to import numpy

# Just to demonstrate that we have zmq in the environment as well
require('pyzmq==13.1.0')
import zmq

from mpi4py import MPI
import h5py
import numpy as np
import socket

import time

import logging
logging.basicConfig(level=0,format=' %(asctime)s.%(msecs)03d %(threadName)-16s %(levelname)-6s %(message)s', datefmt='%H:%M:%S')

import magnets
from genome_tools import ID_BCell
import field_generator as fg

import random

def mutations(c, e_star, fitness, scale):
    inverse_proportional_hypermutation =  abs(((1.0-(e_star/fitness)) * c) + c)
    a = random.random()
    b = random.random()
    hypermacromuation = abs((a-b) * scale)
    return int(inverse_proportional_hypermutation + hypermacromuation)

import optparse

usage = "%prog [options] run_directory"
parser = optparse.OptionParser(usage=usage)
parser.add_option("-f", "--fitness", dest="fitness", help="Set the target fitness", default=0.0, type="float")
parser.add_option("-p", "--processing", dest="processing", help="Set the total number of processing units per file", default=5, type="int")
parser.add_option("-n", "--numnodes", dest="nodes", help="Set the total number of nodes to use", default=10, type="int")
parser.add_option("-s", "--setup", dest="setup", help="set number of genomes to create in setup mode", default=5, type='int')
parser.add_option("-i", "--info", dest="id_filename", help="Set the path to the id data", default='/dls/tmp/ssg37927/id/lookup/id.json', type="string")
parser.add_option("-l", "--lookup", dest="lookup_filename", help="Set the path to the lookup table", default='/dls/tmp/ssg37927/id/lookup/unit.h5', type="string")
parser.add_option("-m", "--magnets", dest="magnets_filename", help="Set the path to the magnet description file", default='/dls/tmp/ssg37927/id/lookup/magnets.mag', type="string")
parser.add_option("-a", "--maxage", dest="max_age", help="Set the maximum age of a genome", default=10, type='int')
parser.add_option("--param_c", dest="c", help="Set the OPT-AI parameter c", default=10.0, type='float')
parser.add_option("--param_e", dest="e", help="Set the OPT-AI parameter eStar", default=0.0, type='float')
parser.add_option("--param_scale", dest="scale", help="Set the OPT-AI parameter scale", default=10.0, type='float')
parser.add_option("-r", "--restart", dest="restart", help="Don't recreate initial data", action="store_true", default=False)
parser.add_option("--iterations", dest="iterations", help="Number of Iterations to run", default=1, type='int')

(options, args) = parser.parse_args()

rank = MPI.COMM_WORLD.rank  # The process ID (integer 0-3 for 4-process run)
size = MPI.COMM_WORLD.size  # The number of processes in the job.

# Print a little report of what we have loaded
if (rank == 0):
    logging.debug("mpi5py loaded: \n\t", MPI)
    logging.debug("h5py loaded:   \n\t", h5py)
    logging.debug("zmq loaded:    \n\t", zmq)

MPI.COMM_WORLD.barrier()

# get the hostname
ip = socket.gethostbyname(socket.gethostname())

logging.debug("Process %d ip address is : %s" % (rank, ip))


logging.debug("Loading magnets")
mags = magnets.Magnets()
mags.load(options.magnets_filename)

#epoch_path = os.path.join(args[0], 'epoch')
#next_epoch_path = os.path.join(args[0], 'nextepoch')
# start by creating the directory to put the initial population in 

population = []
# make the initial population
for i in range(options.setup):
    # create a fresh maglist
    maglist = magnets.MagLists(mags)
    maglist.shuffle_all()
    genome = ID_BCell(options.id_filename, options.lookup_filename, options.magnets_filename)
    genome.create(maglist)
    population.append(genome)

# gather the population
trans = []
for i in range(size):
    trans.append(population)

allpop = MPI.COMM_WORLD.alltoall(trans) 

newpop = []
for pop in allpop:
    newpop += pop

newpop.sort(key=lambda x: x.fitness)

newpop = newpop[options.setup*rank:options.setup*(rank+1)]

for genome in newpop:
    logging.debug("genome fitness is %f" % (genome.fitness))

# now run the processing
for i in range(options.iterations):
    
    logging.debug("Starting itteration %i" % (i))

    nextpop = []

    for genome in newpop:
                
        # now we have to create the offspring
        # TODO this is for the moment
        number_of_children = options.setup
        number_of_mutations = mutations(options.c, options.e, genome.fitness, options.scale)
        children = genome.generate_children(number_of_children, number_of_mutations)
        
        # now save the children into the new file
        for child in children:
            nextpop.append(child)
        
        # and save the original
        nextpop.append(genome)
    
    # gather the population
    trans = []
    for i in range(size):
        trans.append(nextpop)
    
    allpop = MPI.COMM_WORLD.alltoall(trans) 
    
    newpop = []
    for pop in allpop:
        newpop += pop
    
    newpop.sort(key=lambda x: x.fitness)
    
    newpop = newpop[options.setup*rank:options.setup*(rank+1)]
    
    #Checkpoint best solution
    if rank == 0:
        newpop[0].save(args[0])
    
    for genome in newpop:
        logging.debug("genome fitness is %f" % (genome.fitness))
        

# gather the population
trans = []
for i in range(size):
    trans.append(nextpop)

allpop = MPI.COMM_WORLD.alltoall(trans) 

newpop = []
for pop in allpop:
    newpop += pop

newpop.sort(key=lambda x: x.fitness)

newpop = newpop[options.setup*rank:options.setup*(rank+1)]

#Checkpoint best solution
if rank == 0:
    newpop[0].save(args[0])