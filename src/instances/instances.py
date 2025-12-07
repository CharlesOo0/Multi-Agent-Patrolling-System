from dataclasses import dataclass
from typing import List, Tuple
import json

# changer config pour rajoute le nom de l'instance agent et event
# changer setting pour rajouter l'ui des instances agent 
# changer fun init des position dans algo 

#chercher ou modifier pour event 

@dataclass
class Instance:
    name :str
    id:int
    
    
@dataclass
class InstanceAgent(Instance):
    
    nb_agent:int
    position: List[Tuple[int, int]]
    map_name: str
    
@dataclass
class InstanceEvent(Instance):
    #TODO
    event_type: str
    
    

class InstanceManager:
    instancesJSON= "src\instances\instances.json"
    
    def __init__(self):
        self.agent_instances : List[Instance]= []
        self.event_instances: List[Instance]= []
        with open(self.instancesJSON, "r") as eventfile:
            self.manager = json.load(eventfile)
        self.readJSON()
        
    def readJSON(self):
        # iterate over all type of instances
        for i in self.manager:
            temp : Instance
            #iterate over all agent instances
            if i == "agents":
                for agent in self.manager[i]:
                    temp = InstanceAgent(name=agent["name"],
                                         id=agent["id"],
                                         nb_agent=agent["nb_agent"]
                                         ,map_name=agent["map_name"],
                                         position=self.readPosition(agent["position"]))
                    self.agent_instances.append(temp)
            #iterate over all event instances
            elif i == "events":
                for event in self.manager[i]:
                    temp = InstanceEvent(name=event["name"],
                                         id=event["id"],
                                         event_type=event["event_type"])
                    self.event_instances.append(temp)
                    
    # to have the position tuple (x,y) and not [x,y] as given by the JSON        
    def readPosition(self,position):
        positions : List[Tuple[int, int]] = []
        for pos in position:
            positions.append((pos[0],pos[1]))
        return positions
            
            
    
    def getAllInstances(self):
        return  self.event_instances + self.agent_instances
    
    def getAllAgentInstances(self):
         return self.agent_instances
     
    def getAllAgentInstancesName(self):
        return [ agent.name for agent in self.agent_instances ] + ["no instance"]
     
    def getAllAgentInstancesNameByMap(self, map_name):
        return [ agent.name for agent in self.agent_instances if (agent.map_name == map_name) ] + ["no instance"]
    
    def getNumAgentFromInstance(self, instance_name):
        return next((agent.nb_agent for agent in self.agent_instances if (agent.name == instance_name)))
    
    def getPositiontFromInstance(self, instance_name):
       return next((agent.position for agent in self.agent_instances if (agent.name == instance_name)))
     
    def getAllEventInstances(self):
         return  self.event_instances 
     
    def getAllEventInstancesName(self):
         return [ event.name for event in self.event_instances ] + ["no instance"]
     
    def getAgentInstancesByMap(self, map_name):
        return [ i for i in self.agent_instances if (i.map_name == map_name)]
    
    def addNewInstance(self,instance, type):
        if type=="event":
            self.event_instances.append(instance)
        elif type == "agent":
            self.agent_instances.append(instance)
        self.writeJSON()
        
    def writeJSON(self):
        toJSON = {
            "agents": self.agent_instances,
            "events": self.event_instances
        }
        with open(self.instancesJSON, "w") as outfile:
            json.dump(toJSON, outfile,default=vars, indent=4)
        outfile.close()
            
    

#test = InstanceManager()
#print(test.getAllAgentInstancesName())
#self.agent_instances.append(InstanceAgent(name="name",id=5,nb_agent=15,map_name="map_name",position=[(4,5),(6,7)]))