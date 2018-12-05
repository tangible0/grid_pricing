#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uses the t4 model (parameterized by t, and modified demand)
author: Hakan Hekimgil, Jafar Chaab
"""

import numpy as np
import modelt4

customer = 1
initdis = 900
greedystat = False


# model setup
ntimeslots = modelt4.ntimeslots
#disstates = np.arange(0,2100,100)
disstates = list(range(0,25100,100))
maxdisseen = 0
ndisstates = len(disstates)
nstates = (ntimeslots+1) * ndisstates
actions = np.round(np.arange(2.4, 8.3, 0.1), 1)
nactions = len(actions)
#minprice = modelt2.k1 * min(modelt2.wholepricedata)
#possibleactions = {t:[a for a in range(nactions) if nactions[a] >= modelt2.k1 * modelt2.wholeprice(t) and nactions[a] <= modelt2.k2 * modelt2.wholeprice(t)] for t in range(1,ntimeslots+1)}
epsilon = 0.5   # rate for exploration
discount = 0.9  # discount rate for future rewards
alpha = 0.1     # learning rate

# returns time from state as a 1-index period number
def tfs(state):
    return (state % (ntimeslots+1)) + 1

# returns dissatisfaction from state as an index format
def dfs(state):
    return state//(ntimeslots+1)

# returns the state code for time period and dissatisfaction
def getstate(t,dis):
    return (t - 1) + disstates.index(round(min(dis,disstates[-1]),-2)) * (ntimeslots+1)

# returns the code for next state given the current state and the price action
def nextstate(state, price):
    disidx = dfs(state)
    t = tfs(state)
    nextdis = min(modelt4.cocoef*disstates[disidx] + modelt4.phi(t, customer, price), disstates[-1])
    return getstate(t+1,nextdis)

def getdisstate(values):
    return [disstates.index(round(val,-2)) for val in values]

def actionablestatesfrom(state):
    global maxdisseen
    t = tfs(state)
    nextdisvalues = np.round(
            [modelt4.cocoef*disstates[dfs(state)]+modelt4.phi(t,customer,a) for a in actions if a >= modelt4.wholeprice(t)], -2)
    maxdisseen = max(maxdisseen, max(nextdisvalues))
    nextdisvalues = [min(value, disstates[-1]) for value in nextdisvalues]
    idx = getdisstate(nextdisvalues)
    return list(set([(t) + i * (ntimeslots+1) for i in idx]))

def reward(state,n,price):
    return modelt4.obj(tfs(state),n,price) - (1-modelt4.rho) * disstates[dfs(state)]
#    return modelt4.obj(tfs(state),n,price) - disstates[dfs(state)]

def takeaction(state,n,greedy = True):
    if greedy and np.random.random() <= min(epsilon, 10/iterations):
        price = 0
        while price < modelt4.wholeprice(tfs(state)):
            randomaction = np.random.randint(nactions)
            price = actions[randomaction]
        #randomprice = actions[randomaction]
        return randomaction
    else:
        bestaction = np.argmax(qmatrix[state,:])
        #bestprice = actions[bestaction]
        return bestaction

# initialization
timeslot = 1
iterations = 0
qmatrix = np.zeros([nstates,nactions]) # one extra row
qprev = 1000*np.ones([nstates,nactions]) # one extra row
delta = 1
convergence = []
qconvergence = []
initstate = getstate(1,initdis)
#qmatrix = np.full([ntimeslots+1,nactions], -np.inf) # one extra row


# Q-Learning loop
while np.max(np.abs(qmatrix-qprev)) > delta:
    curstate = initstate
    iterations += 1
    if iterations % 20 == 0:
        print("iteration {:,}; delta: {:}...".format(iterations, np.max(np.abs(qmatrix-qprev))))
    qprev = qmatrix.copy()
    for t in range(1,ntimeslots+1):
        for action in range(nactions):
            # IMPORTANT REMINDER:
            # The functions use t as it is so reward(t,n,p) refers to time t
            # Arrays use t with 0-index addressing so qmatrix[t-1:] refers to time t
            if t == ntimeslots:
                futureq = 0
            else:
                futureq = np.max(qprev[actionablestatesfrom(nextstate(curstate,actions[action])),:])
            qmatrix[curstate,action] = (
                    (1 - alpha ) * qprev[curstate,action] + 
                    alpha * (
                            reward(curstate,customer,actions[action]) + 
                            discount * futureq))
        actiontotake = takeaction(curstate, customer, greedy=greedystat)
        curstate = nextstate(curstate, actions[actiontotake])
    convergence.append(np.max(np.abs(qmatrix-qprev)))
    qconvergence.append(np.mean(np.abs(qmatrix)))
print("finished at iteration {:,}, with a delta of {:}...".format(iterations, np.max(np.abs(qmatrix-qprev))))
#    totalreward = 0
#    action = np.argmax(qmatrix[t-1,:])
#    aprice = actions[action]
#    reward = modelt2.obj(timeslot,1,aprice)

#retailprices = [ actions[x] for x in np.argmax(qmatrix[:-1,:], axis=1)]
#dis = [modelt4.phi(t,customer,retailprices[t-1]) for t in range(1,25)]
bestpolicy = list()
dislist = list()
policystate = initstate
action = np.argmax(qmatrix[policystate,:])
price = actions[action]
dislist.append(initdis)
bestpolicy.append(price)
cumdislist = [dislist[0]]
sar = [(policystate, price, reward(policystate, customer, price))]
#policystate = np.argmax(qmatrix[:,:], axis=1)
for t in range(2,25):
    policystate = nextstate(policystate, price)
    action = np.argmax(qmatrix[policystate,:])
    price = actions[action]
    dislist.append(modelt4.phi(t,customer,price))
    cumdislist.append(disstates[dfs(policystate)])
    bestpolicy.append(price)
    sar.append((policystate, price, reward(policystate, customer, price)))
print(bestpolicy)




def policyreward(policy, n, initstate=initstate):
    totalrewards = 0
    state = initstate
    for t in range(1,25):
        totalrewards += reward(state, customer, policy[t-1])
        state = nextstate(state, policy[t-1])
    return totalrewards

# VISUALISE INPUT AND OUTPUT DATA

# Combined plot
def plotresults():
    import matplotlib.pyplot as plt
    trange = list(range(1,25))
    barw = 0.25
    trange1 = [t-barw for t in trange]
    fig, ax1 = plt.subplots()
    p1 = plt.bar(trange1, [modelt4.edemandcurt(t,customer) for t in trange], width=barw, color="blue")
    p2 = plt.bar(trange, [modelt4.econscurt(t,customer,bestpolicy[t-1]) for t in trange], width=barw, color="red")
    plt.title("Customer {:}".format(customer))
    plt.xlabel("Time slot")
    ax1.set_ylabel("Electricity (kWh)")
    plt.yticks(list(range(0,14,2)))
    plt.xlim(0.3,24.7)
    plt.xticks(list(range(1,25)))
    ax2 = ax1.twinx()
    p3 = plt.plot(trange, modelt4.wholepricedata, "o-g")
    p4 = plt.plot(trange, bestpolicy, "o-r")
    ax2.set_ylabel("Price (ȼ/kWh)")
    plt.yticks(list(range(0,10)))
    plt.legend((p1[0], p2[0], p3[0], p4[0]), 
               ("Energy demand", "Energy consumption", "Wholesale price", "Retail price"), 
               loc=2)
    fig.tight_layout()
    plt.show()
    return

def plotconvergence():
    import matplotlib.pyplot as plt
    plt.plot(convergence)
    plt.show()
    plt.plot(qconvergence)
    plt.show()
    return

print(initdis, modelt4.dmul[customer], modelt4.cocoef, greedystat, maxdisseen)
#showwholepricing()
#showdemand()
plotresults()