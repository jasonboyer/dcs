from pybrain.rl.agents.learning import LearningAgent

# Learning agent

class DogAgent(LearningAgent):
    def __init__(self, table, learner = None):
        super().__init__(table, learner)

    # def getAction(self):

    # def integrateObservation(self):

