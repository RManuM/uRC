'''
Created on 11.07.2014

@author: mend_ma
'''

from lxml import etree
import os
import logging

class Autobahn_Dataparser(object):
    '''
    classdocs
    '''
    _definitions = {}
    _responses = {}

    def __init__(self, LOGGER, filename=None):
        '''
        Constructor
        '''
        loaded = False
        ## Loading definition
        if filename is not None:
            path = os.path.abspath(filename)
            if os.path.exists(path):
                if os.path.isfile(path):
                    root = etree.parse(filename).getroot()
                    LOGGER.info("loading definitions from " + str(path))
                    loaded = True
        if not loaded:
            LOGGER.warn("no valid defintions-file found at " + str(path))
            xml_definition = """
            <root>
                <topic name='uRC.testing.receiver.data'>
                    <attribute name='message'>string</attribute>
                    <attribute name='index'>int</attribute>
                </topic>
                
                <slot name='uRC.testing.receiver.rpc'>
                    <attribute name='ping'>string</attribute>
                    <attribute name='index'>int</attribute>
                </slot>
            </root>"""
            root = etree.fromstring(xml_definition)
            print etree.tostring(root, pretty_print=True)
            
        for element in root.iter("topic"):
            definition = self.__generateDefinition(element)
            self._definitions[element.get("name")] = definition
            
        for element in root.iter("slot"):
            definition = self.__generateDefinition(element)
            self._definitions[element.get("name")] = definition
            
        for element in root.iter("response"):
            definition = self.__generateDefinition(element)
            self._responses[element.get("name")] = definition
            
    def __generateDefinition(self, element):
        result = {}
        for entry in element:
            opt = str(entry.get("optional")).lower() == "true"
            if len(entry) == 0:
                result[entry.get("name")] = {"type":self.__convertTypeNames(entry.text), "optional":opt}
            else:
                result[entry.get("name")] = {"sub_entry":self.__generateDefinition(entry), "optional":opt}
        return result
    
    def __convertTypeNames(self, name):
        if name.lower() == "int":
            return int
        elif name.lower() == "float":
            return float
        elif name.lower() == "string":
            return str
        elif name.lower() == "boolean":
            return bool
        else:
            return None
        
    def parse_response(self, url, data):
        definition = self._responses[url]
        return self._parse(url, data, definition)
    
    def parse(self, url, data):
        definition = self._definitions[url]
        result = self._parse(url, data, definition)
        return result
        
    def _parse(self, url, data, definition):
        def parseEntry(url, data, definition):
            for key, value in definition.items():
                if not type(data)==type(dict()):
                    err_code, err_msg = 1, "For " + url + " key " + key + " not a dictionary"
                    raise ValueError(err_code, err_msg)
                if not data.has_key(key):
                    if value["optional"] == False:
                        err_code, err_msg = 1, "For " + url + " key " + key + " missing"
                        raise ValueError(err_code, err_msg)
                else:
                    if value.has_key("type"):
                        if not type(data[key]) == value["type"]:
                            err_code, err_msg = 1, "For " + url + " key " + key + " invalid type given"
                            raise ValueError(err_code, err_msg)
                    elif value.has_key("sub_entry"):
                        if type(value["sub_entry"])==dict:
                            parseEntry(url, data[key], value["sub_entry"])
                        else:
                            err_code, err_msg = 1, "For " + url + " key " + key + " missing"
                            raise ValueError(err_code, err_msg)
            
        try:
            parseEntry(url, data, definition)            
        except ValueError as e:
            print "ValueError:{}".format(e)
            return False
        except Exception as e:
            print "Exception:{}".format(e)
            return False
        else:
            return True 
        
    def generate_sample_topic(self, url):
        definition = self._definitions[url]
        return self.generate_sample_json(url, definition)

    def generate_sample_answer(self, url):
        definition = self._responses[url]
        return self.generate_sample_json(url, definition)
        
    def generate_sample_json(self, url, definition):
        def getSpaces(count):
            result = ""
            for i in range(count):  # @UnusedVariable
                result += "\t"
            return result
        def parse_layer(element, layer):
            result = getSpaces(layer) + "{"
            index = 0
            for key, value in element.items():
                if index > 0:
                    result += ",\n"
                    result += getSpaces(layer)
                index+=1
                if value.has_key("type"):
                    result += "\"" + key + "\":" + value["type"].__name__
                elif value.has_key("sub_entry"):
                    result += "\"" + key + "\":\n" + parse_layer(value, layer+1)
                if value["optional"]:
                    result += "(opt)"
            result += "\n" + getSpaces(layer) + "}"
            return result
        result = parse_layer(definition,0)
        return result
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = Autobahn_Dataparser(logging.getLogger("parser"), filename="../../../config/definitions.xml")
    print parser.generate_sample_topic("uRC.testing.receiver.data")
    print parser.generate_sample_topic("uRC.testing.receiver.rpc")
    print parser.generate_sample_answer("uRC.testing.receiver.rpc")
    