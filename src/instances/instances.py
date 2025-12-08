from dataclasses import dataclass
from typing import List, Tuple
import json

@dataclass
class Instance:
    name :str
    id:int
    nb_agent:int
    position: List[Tuple[int, int]]
    map_name: str
    event_type: str
    
    

class InstanceManager:
    instancesJSON= "src\instances\instances.json"
    
    def __init__(self):
        
        self.instances: List[Instance]= []
        
        with open(self.instancesJSON, "r") as eventfile:
            self.manager = json.load(eventfile)
        self.readJSON()
        
    def readJSON(self):
        # iterate over all type of instances
        for i in self.manager:
            temp : Instance
            for instance in self.manager[i]:
                temp = Instance(name=instance["name"],
                                         id=instance["id"],
                                         nb_agent=instance["nb_agent"]
                                         ,map_name=instance["map_name"],
                                         position=self.readPosition(instance["position"]),
                                         event_type=instance["event_type"])
                self.instances.append(temp)
                    
    # to have the position tuple (x,y) and not [x,y] as given by the JSON        
    def readPosition(self,position):
        positions : List[Tuple[int, int]] = []
        for pos in position:
            positions.append((pos[0],pos[1]))
        return positions
            
    def getAllInstances(self):
        return  self.instances
    
    def getAlltInstancesName(self):
        return [ instance.name for instance in self.instances ] + ["no instance"]
    
    def getAllInstancesNameByMap(self, map_name):
        return [ instance.name for instance in self.instances if (instance.map_name == map_name) ] + ["no instance"]
    
    def getNumAgentFromInstance(self, instance_name):
        return next((instance.nb_agent for instance in self.instances if (instance.name == instance_name)))
    
    def getPositiontFromInstance(self, instance_name):
       return next((instance.position for instance in self.instances if (instance.name == instance_name)))
    
    def addNewInstance(self,instance):
        self.instances.append(instance)
        self.writeJSON()
    
    def writeJSON(self):
        toJSON = {
            "instance": self.instances,
        }
        with open(self.instancesJSON, "w") as outfile:
            json.dump(toJSON, outfile,default=vars, indent=4)
        outfile.close()
            
    

#test = InstanceManager()
#print(test.getAlltInstancesName())