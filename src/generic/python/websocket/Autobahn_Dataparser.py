'''
Created on 11.07.2014

@author: mend_ma
'''

from lxml import etree
import os

class Autobahn_Dataparser(object):
    '''
    classdocs
    '''
    _definitions = {}

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
            
        for element in root:
            definition = self.__generateDefinition(element)
            self._definitions[element.get("name")] = definition
            
    def __generateDefinition(self, element):
        result = {}
        for entry in element:
            if len(entry) == 0:
                result[entry.get("name")] = {"type":self.__convertTypeNames(entry.text)}
            else:
                result[entry.get("name")] = self.__generateDefinition(entry)
        return result
    
    def __convertTypeNames(self, name):
        if name.lower() == "int":
            return int
        elif name.lower() == "float":
            return float
        elif name.lower() == "string":
            return str
        else:
            return None
    
    def parse(self, url, data):
        def parseEntry(url, data, definition):
            for key, value in definition.items():
                if not type(data)==type(dict()):
                    err_code, err_msg = 1, "For " + url + " key " + key + " not a dictionary"
                    raise ValueError(err_code, err_msg)
                if not data.has_key(key):
                    err_code, err_msg = 1, "For " + url + " key " + key + " missing"
                    raise ValueError(err_code, err_msg)
                else:
                    if value.has_key("type"):
                        if not type(data[key]) == value["type"]:
                            err_code, err_msg = 1, "For " + url + " key " + key + " missing"
                            raise ValueError(err_code, err_msg)
                    else:
                        if type(value)==dict:
                            parseEntry(url, data[key], definition[key])
        
        definitions = self._definitions[url]
        try:
            parseEntry(url, data, definitions)
        except ValueError as e:
            print "ValueError:{}".format(e)
            return False
        except Exception as e:
            print "Exception:{}".format(e)
        else:
            return True 
        
    def generate_sample_json(self, url):
        definition = self._definitions[url]
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
                else:
                    result += "\"" + key + "\":\n" + parse_layer(value, layer+1)
            result += "\n" + getSpaces(layer) + "}"
            return result
        result = parse_layer(definition,0)
        return result
        
if __name__ == "__main__":
    parser = Autobahn_Dataparser()