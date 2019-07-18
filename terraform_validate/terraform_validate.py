import hcl
import os
import codecs
import re
import traceback
import json
import logging


class TerraformPropertyList:

    def __init__(self, validator):
        self.properties = []
        self.validator = validator

    def tfproperties(self):
        return self.properties

    def property(self, property_name):
        propList = TerraformPropertyList(self.validator)
        for property in self.properties:
            pvList = []
            if type(property.property_value) is list:
                pvList = property.property_value
            else:
                pvList.append(property.property_value)

            for pv in pvList:
                if property_name in pv.keys():
                    propList.properties.append(TerraformProperty(property.resource_type,
                                               "{0}.{1}".format(property.resource_name, property.property_name),
                                               property_name,
                                               pv[property_name],
                                               property.moduleName,
                                               property.fileName))
                elif self.validator.raise_error_if_property_missing:
                    self.validator.preprocessor.add_failure(
                        "[{0}.{1}] should have property: '{2}'".format(property.resource_type, "{0}.{1}".format(property.resource_name, property.property_name), property_name),
                        property.moduleName,
                        property.fileName,
                        self.validator.severity)

        return propList

    def should_equal_case_insensitive(self, expected_value):
        self.should_equal(expected_value, True)

    def should_equal(self, expected_value, caseInsensitive=False):
        for property in self.properties:

            expected_value = self.int2str(expected_value)
            property.property_value = self.int2str(property.property_value)
            expected_value = self.bool2str(expected_value)
            property.property_value = self.bool2str(property.property_value)

            if caseInsensitive:
                # make both actual and expected lower case so case won't matter
                pv = property.property_value.lower()
                ev = expected_value.lower()
            else:
                pv = property.property_value
                ev = expected_value

            if pv != ev:
                self.validator.preprocessor.add_failure("[{0}.{1}.{2}] should be '{3}'. Is: '{4}'".format(property.resource_type,
                                                                                                          property.resource_name,
                                                                                                          property.property_name,
                                                                                                          expected_value,
                                                                                                          property.property_value),
                                                        property.moduleName,
                                                        property.fileName,
                                                        self.validator.severity)

    def should_not_equal_case_insensitive(self, expected_value):
        self.should_not_equal(expected_value, True)

    def should_not_equal(self, expected_value, caseInsensitive=False):
        for property in self.properties:

            property.property_value = self.int2str(property.property_value)
            expected_value = self.int2str(expected_value)
            expected_value = self.bool2str(expected_value)
            property.property_value = self.bool2str(property.property_value)

            if caseInsensitive:
                # make both actual and expected lower case so case won't matter
                pv = property.property_value.lower()
                ev = expected_value.lower()
            else:
                pv = property.property_value
                ev = expected_value

            if pv == ev:
                self.validator.preprocessor.add_failure("[{0}.{1}.{2}] should not be '{3}'. Is: '{4}'".format(property.resource_type,
                                                                                                              property.resource_name,
                                                                                                              property.property_name,
                                                                                                              expected_value,
                                                                                                              property.property_value),
                                                        property.moduleName,
                                                        property.fileName,
                                                        self.validator.severity)

    def list_should_contain(self, values_list):
        if type(values_list) is not list:
            values_list = [values_list]

        for property in self.properties:

            values_missing = []
            for value in values_list:
                if value not in property.property_value:
                    values_missing.append(value)

            if len(values_missing) != 0:
                if type(property.property_value) is list:
                    property.property_value = [str(x) for x in property.property_value]  # fix 2.6/7
                self.validator.preprocessor.add_failure("[{0}.{1}.{2}] '{3}' should contain '{4}'.".format(property.resource_type,
                                                                                                           property.resource_name,
                                                                                                           property.property_name,
                                                                                                           property.property_value,
                                                                                                           values_missing),
                                                        property.moduleName,
                                                        property.fileName,
                                                        self.validator.severity)

    def list_should_not_contain(self, values_list):
        if type(values_list) is not list:
            values_list = [values_list]

        for property in self.properties:

            values_missing = []
            for value in values_list:
                if value in property.property_value:
                    values_missing.append(value)

            if len(values_missing) != 0:
                if type(property.property_value) is list:
                    property.property_value = [str(x) for x in property.property_value]  # fix 2.6/7
                self.validator.preprocessor.add_failure("[{0}.{1}.{2}] '{3}' should not contain '{4}'.".format(property.resource_type,
                                                                                                               property.resource_name,
                                                                                                               property.property_name,
                                                                                                               property.property_value,
                                                                                                               values_missing),
                                                        property.moduleName,
                                                        property.fileName,
                                                        self.validator.severity)

    def should_have_properties(self, properties_list):
        if type(properties_list) is not list:
            properties_list = [properties_list]

        for property in self.properties:
            property_names = property.property_value.keys()
            for required_property_name in properties_list:
                if required_property_name not in property_names:
                    self.validator.preprocessor.add_failure("[{0}.{1}.{2}] should have property: '{3}'".format(property.resource_type,
                                                                                                               property.resource_name,
                                                                                                               property.property_name,
                                                                                                               required_property_name),
                                                            property.moduleName,
                                                            property.fileName,
                                                            self.validator.severity)

    def should_not_have_properties(self, properties_list):
        if type(properties_list) is not list:
            properties_list = [properties_list]

        for property in self.properties:
            property_names = property.property_value.keys()
            for excluded_property_name in properties_list:
                if excluded_property_name in property_names:
                    self.validator.preprocessor.add_failure("[{0}.{1}.{2}] should not have property: '{3}'".format(property.resource_type,
                                                                                                                   property.resource_name,
                                                                                                                   property.property_name,
                                                                                                                   excluded_property_name),
                                                            property.moduleName,
                                                            property.fileName,
                                                            self.validator.severity)

    def find_property(self, regex):
        list = TerraformPropertyList(self.validator)
        for property in self.properties:
            for nested_property in property.property_value:
                if self.validator.matches_regex_pattern(nested_property, regex):
                    list.properties.append(TerraformProperty(property.resource_type,
                                           "{0}.{1}".format(property.resource_name, property.property_name),
                                           nested_property,
                                           property.property_value[nested_property],
                                           property.moduleName,
                                           property.fileName))
        return list

    def should_match_regex(self, regex):
        for property in self.properties:
            if not self.validator.matches_regex_pattern(property.property_value, regex):
                self.validator.preprocessor.add_failure("[{0}.{1}] should match regex '{2}'".format(property.resource_type, "{0}.{1}".format(property.resource_name, property.property_name), regex),
                                                        property.moduleName,
                                                        property.fileName,
                                                        self.validator.severity)

    def should_contain_valid_json(self):
        for property in self.properties:
            try:
                json.loads(property.property_value)
            except:
                self.validator.preprocessor.add_failure("[{0}.{1}.{2}] is not valid json".format(property.resource_type, property.resource_name, property.property_name),
                                                        property.moduleName,
                                                        property.fileName,
                                                        self.validator.severity)

    def bool2str(self, bool):
        if str(bool).lower() in ["true"]:
            return "True"
        if str(bool).lower() in ["false"]:
            return "False"
        return bool

    def int2str(self, property_value):
        if type(property_value) is int:
            property_value = str(property_value)
        return property_value


class TerraformProperty:

    def __init__(self, resource_type, resource_name, property_name, property_value, moduleName, fileName):
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.property_name = property_name
        self.property_value = property_value
        self.moduleName = moduleName
        self.fileName = fileName


class TerraformResource:

    def __init__(self, type, name, config, fileName, moduleName):
        self.type = type
        self.name = name
        self.config = config
        self.fileName = fileName
        self.moduleName = moduleName


class TerraformResourceList:

    def __init__(self, validator, requestedResourceType, resourceTypes, resources):
        self.validator = validator
        self.resource_list = []
        self.requestedResourceType = requestedResourceType

        resourcesByType = {}
        for resourceName in resources:
            resource = resources[resourceName]
            resourceType = resource.type
            resourcesByType[resourceType] = resourcesByType.get(resourceType, {})
            resourcesByType[resourceType][resourceName] = resource.config

        if type(requestedResourceType) is str:
            resourceTypes = []
            for resourceType in resourcesByType:
                if validator.matches_regex_pattern(resourceType, requestedResourceType):
                    resourceTypes.append(resourceType)
        elif requestedResourceType is not None:
            resourceTypes = requestedResourceType

        for resourceType in resourceTypes:
            if resourceType in resourcesByType.keys():
                for resourceName in resourcesByType[resourceType]:
                    self.resource_list.append(
                        TerraformResource(resourceType, resourceName, resourcesByType[resourceType][resourceName], resources[resourceName].fileName, resources[resourceName].moduleName))

        self.resource_types = resourceTypes

    def property(self, property_name):
        list = TerraformPropertyList(self.validator)
        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                if property_name in resource.config.keys():
                    list.properties.append(TerraformProperty(resource.type, resource.name, property_name, resource.config[property_name], resource.moduleName, resource.fileName))
                elif self.validator.raise_error_if_property_missing:
                    self.validator.preprocessor.add_failure("[{0}.{1}] should have property: '{2}'".format(resource.type, resource.name, property_name),
                                                            resource.moduleName, resource.fileName, self.validator.severity)

        return list

    def find_property(self, regex):
        list = TerraformPropertyList(self.validator)
        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                for property in resource.config:
                    if self.validator.matches_regex_pattern(property, regex):
                        list.properties.append(TerraformProperty(resource.type,
                                                                 resource.name,
                                                                 property,
                                                                 resource.config[property],
                                                                 resource.moduleName,
                                                                 resource.fileName))
        return list

    def with_property(self, property_name, regex):
        list = TerraformResourceList(self.validator, None, self.resource_types, {})

        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                for property in resource.config:
                    if property == property_name:
                        tf_property = TerraformProperty(resource.type, resource.name, property_name, resource.config[property_name], resource.moduleName, resource.fileName)
                        if self.validator.matches_regex_pattern(tf_property.property_value, regex):
                            list.resource_list.append(resource)

        return list

    def should_not_exist(self):
        for terraformResource in self.resource_list:
            if terraformResource.type == self.requestedResourceType:
                self.validator.preprocessor.add_failure("[{0}] should not exist. Found in resource named {1}".format(self.requestedResourceType, terraformResource.name),
                                                        terraformResource.moduleName, terraformResource.fileName, self.validator.severity)

    def should_have_properties(self, properties_list):
        if type(properties_list) is not list:
            properties_list = [properties_list]

        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                property_names = resource.config.keys()
                for required_property_name in properties_list:
                    if required_property_name not in property_names:
                        self.validator.preprocessor.add_failure("[{0}.{1}] should have property: '{2}'".format(
                            resource.type, resource.name, required_property_name),
                            resource.moduleName, resource.fileName, self.validator.severity)

    def should_not_have_properties(self, properties_list):
        if type(properties_list) is not list:
            properties_list = [properties_list]

        if len(self.resource_list) > 0:
            for resource in self.resource_list:
                property_names = resource.config.keys()
                for excluded_property_name in properties_list:
                    if excluded_property_name in property_names:
                        self.validator.preprocessor.add_failure("[{0}.{1}] should not have property: '{2}'".format(resource.type, resource.name, excluded_property_name),
                                                                resource.moduleName, resource.fileName, self.validator.severity)

    def name_should_match_regex(self, regex):
        for resource in self.resource_list:
            if not self.validator.matches_regex_pattern(resource.name, regex):
                self.validator.preprocessor.add_failure("[{0}.{1}] name should match regex: '{2}'".format(resource.type, resource.name, regex),
                                                        resource.moduleName, resource.fileName, self.validator.severity)


class Validator:

    # default severity is high
    severity = "high"
    preprocessor = None

    def __init__(self):
        self.raise_error_if_property_missing = False

    def resources(self, type):
        resources = self.terraform.get('resource', {})

        return TerraformResourceList(self, type, None, resources)

    def error_if_property_missing(self):
        self.raise_error_if_property_missing = True

    # generator that loops through all files to be scanned (stored internally in fileName; returns self (Validator) but sets self.fileName and self.terraform
    def get_terraform_files(self):
        for self.fileName, self.terraform in self.preprocessor.modulesDict.items():
            yield self

    def matches_regex_pattern(self, variable, regex):
        return not (self.get_regex_matches(regex, variable) is None)

    def get_regex_matches(self, regex, variable):
        if regex[-1:] != "$":
            regex = regex + "$"

        if regex[0] != "^":
            regex = "^" + regex

        variable = str(variable)
        if '\n' in variable:
            return re.match(regex, variable, re.DOTALL)
        return re.match(regex, variable)

    # this is only used by unit_test.py
    def setTerraform(self, terraform):
        self.terraform = terraform
        self.fileName = "none.tf"


class PreProcessor:

    TF = ".tf"
    UTF8 = "utf8"
    IS_MODULE = "__isModule__"
    PARENT = "__parent__"
    MODULE_NAME = "__ModuleName__"
    FILE_NAME = "__fileName__"
    LOCALS = "locals"
    VARIABLE = "variable"
    OUTPUT = "output"
    RESOURCE = "resource"
    VALUE = "value"
    MODULE = "module"
    SOURCE = "source"
    DEFAULT = "default"
    REGEX_COLON_BRACKET = re.compile('.*:\s*\[.*', re.DOTALL)   # any characters : whitespace [ any characters

    def __init__(self, jsonOutput):
        self.jsonOutput = jsonOutput
        self.variablesFromCommandLine = {}
        self.hclDict = {}
        self.modulesDict = {}
        self.fileNames = {}
        self.passNumber = 1
        self.dummyIndex = 0
        # on 1st pass replace var. with var$.
        # on 2nd pass replace var. and var$. with var!.
        self.braces = ["${", "@{", "!{"]
        self.vars = ["var.", "var@.", "var!."]
        self.locals = ["local.", "local@.", "local!."]
        self.modules = ["module.", "module@.", "module!."]
        self.terraform_workspaces = ["terraform.workspace", "terraform@.workspace", "terraform!.workspace"]
        self.variableFind = [self.braces[0], self.vars[0], self.locals[0], self.modules[0], self.terraform_workspaces[0]]
        self.variableErrorReplacement = [self.braces[1], self.vars[1], self.locals[1], self.modules[1], self.terraform_workspaces[1]]
        self.variableErrorReplacementPass2 = [self.braces[2], self.vars[2], self.locals[2], self.modules[2], self.terraform_workspaces[2]]

    def process(self, path, variablesJsonFilename=None):
        inputVars = {}
        if variablesJsonFilename is not None:
            for fileName in variablesJsonFilename:                
                with codecs.open(fileName, 'r', encoding='utf8') as fp:
                    try:
                        variables_string = fp.read()
                        inputVarsDict = hcl.loads(variables_string)
                        inputVars = {**inputVars, **inputVarsDict}
                    except:
                        self.add_error_force(traceback.format_exc(), "---", fileName, "high")

        # prefix any input variable not containing '.' with 'var.'
        for var in inputVars:
            if "." not in var:
                newVar = "var." + var
                self.variablesFromCommandLine[newVar] = inputVars[var]
            else:
                self.variablesFromCommandLine[var] = inputVars[var]
                
        self.root = None
        self.readDir(path, self.hclDict)

        # all terraform files are now loaded into hclDict (indexed by subdirectory/fileName/terraform structure)
        # process hclDict and load every module into modulesDict
        self.getAllModules(self.hclDict, False)
        # make second pass so variables depending on a previous definition should now be defined
        logging.warning("------------------>>>starting pass 2...")
        self.passNumber = 2
        self.variableFind = self.variableErrorReplacement
        self.variableErrorReplacement = self.variableErrorReplacementPass2
        self.getAllModules(self.hclDict, False)

    def readDir(self, path, d):
        for directory, subdirectories, files in os.walk(path):
            if self.root is None:
                self.root = directory
                i = self.root.rfind(os.path.sep)
                if i != -1:
                    self.root = self.root[i+1:]
                # define root and mark this dictionary as a module since all directories in terraform are modules by default
                self.hclDict[self.root] = {}
                self.hclDict[self.root][self.IS_MODULE] = True
                self.hclDict[self.root][self.PARENT] = None
                self.hclDict[self.root][self.MODULE_NAME] = self.root
                d = self.hclDict[self.root]

            for file in files:
                if file[-3:].lower() == self.TF:
                    # terraform file (ends with .tf)
                    fileName = os.path.join(directory, file)
                    relativeFileName = fileName[len(path):]
                    with codecs.open(fileName, 'r', encoding='utf8') as fp:
                        try:
                            terraform_string = fp.read()
                            if len(terraform_string.strip()) > 0:
                                self.loadFileByDir(fileName, relativeFileName, d, d, terraform_string)
                                self.fileNames[fileName] = fileName
                        except:
                            self.add_error_force(traceback.format_exc(), "---", fileName, "high")

    # load file by directory, marking each directory as a module and setting parent directories
    def loadFileByDir(self, fileName, path, hclSubDirDict, parentDir, terraform_string):
        i = path.find("\\")
        if i == -1:
            # \ not found, try /
            i = path.find("/")
            if i == -1:
                # end of subdirectories; path is a terraform filename; load terraform file into dictionary
                hclSubDirDict[path] = hcl.loads(terraform_string)
                hclSubDirDict[path][self.FILE_NAME] = fileName
                # remove file name from end of path
                t = self.getPreviousLevel(fileName, os.path.sep)
                self.findModuleSources(hclSubDirDict[path], parentDir, t[0])
                return
        if i == 0:
            # found in first character, recursively try again skipping first character
            self.loadFileByDir(fileName, path[1:], hclSubDirDict, parentDir, terraform_string)
        else:
            # get subdirectory
            subdir = path[:i]
            if hclSubDirDict.get(subdir) is None:
                # subdirectory not defined in our dictionary yet so define it
                hclSubDirDict[subdir] = {}
                hclSubDir = hclSubDirDict[subdir]
                # mark this dictionary as a module since all directories in terraform are modules by default
                hclSubDir[self.IS_MODULE] = True
                hclSubDir[self.PARENT] = parentDir
                hclSubDir[self.MODULE_NAME] = subdir
            else:
                hclSubDir = hclSubDirDict[subdir]
            # recursively process next subdirectory
            i += 1
            self.loadFileByDir(fileName, path[i:], hclSubDirDict[subdir], hclSubDir, terraform_string)

    def findModuleSources(self, d, parentDir, currentFileName):
        for key in d:
            # only process module key
            if key == self.MODULE:
                modules = d[key]
                # process all modules
                for moduleName in modules:
                    module = modules[moduleName]
                    # find source parameter
                    for parameter in module:
                        if parameter == self.SOURCE:
                            sourcePath = module[parameter]
                            self.createMissingFromSourcePath(sourcePath, parentDir, currentFileName)

    def createMissingFromSourcePath(self, sourcePath, d, currentFileName):
        # source is local
        while sourcePath != "":
            t = self.getNextLevel(sourcePath, "/")
            currentModule = t[0]
            sourcePath = t[1]
            if currentModule == "..":
                # move up a level
                t = self.getPreviousLevel(currentFileName, os.path.sep)
                currentFileName = t[0]
                if d.get(self.PARENT) is None:
                    # add parent
                    self.dummyIndex += 1
                    parent = {}
                    parent[self.PARENT] = None
                    parent[self.IS_MODULE] = True
                    parent[self.MODULE_NAME] = "dummy" + str(self.dummyIndex)
                    parent[d[self.MODULE_NAME]] = d
                    d[self.PARENT] = parent
                    self.hclDict = parent
                d = d[self.PARENT]
            elif currentModule == ".":
                # current directory; do nothing
                pass
            else:
                # move down to currentModule level
                currentFileName += os.path.sep + currentModule
                md = d.get(currentModule, False)
                if md is False:
                    # create new level
                    d[currentModule] = {}
                    md = d[currentModule]
                    md[self.PARENT] = d
                    md[self.MODULE_NAME] = currentModule
                    md[self.IS_MODULE] = True

                d = md
        # read directory
        self.readDir(currentFileName, d)
        return d

    # get all modules for given dictionary d; pass isModule as True if in a module block
    def getAllModules(self, d, isModule):
        for key in d:
            # ignore parent key
            if key != self.PARENT:
                value = d[key]
                if type(value) is dict:
                    if isModule or self.isModule(value):
                        moduleName = key
                        # load module, resolve variables in it and add it to modules dictionary
                        moduleDict = self.getModule(moduleName)
                        if self.isModule(value):
                            moduleDict[self.PARENT] = d[moduleName][self.PARENT]
                    # recursively get all modules in the nested dictionary in value
                    self.getAllModules(value, key == "module")

    # get given moduleName from modulesDict; find & load it if not there yet
    def getModule(self, moduleName, errorIfNotFound=True, dictToCopyFrom=None, tfDict=None):
        moduleDict = self.modulesDict.get(moduleName)
        if moduleDict is None or (moduleDict[self.VARIABLE] == {} and moduleDict[self.LOCALS] == {} and moduleDict[self.OUTPUT] == {}):
            # not there yet, find it and load it
            moduleDict = self.findModule(moduleName, self.hclDict, dictToCopyFrom, tfDict)
            if moduleDict is None:
                # couldn't find it, log it and create a dummy entry
                if errorIfNotFound:
                    self.logMsg("error", "Couldn't find module " + moduleName)
                moduleDict = self.createModuleEntry(moduleName)
        elif self.passNumber > 1:
            # module found on second pass, re-resolve variables
            self.findModule(moduleName, self.hclDict, dictToCopyFrom, tfDict)

        return moduleDict

    # find given moduleName in given dictionary d; load module attributes and resolve variables in module; last two parameters are all or nothing
    def findModule(self, moduleName, d, dictToCopyFrom=None, tfDict=None):
        # use dictToCopyFrom if provided
        if dictToCopyFrom is not None:
            sourcePath = self.getSourcePath(dictToCopyFrom)
            if sourcePath is not None and not sourcePath.startswith("git::"):
                dd = self.getModuleDictFromSourcePath(sourcePath, tfDict)
                if dd:
                    moduleDict = self.modulesDict.get(dd[self.MODULE_NAME])
                    if moduleDict is None:
                        moduleDict = self.createModuleEntry(dd[self.MODULE_NAME])
                        moduleDict[self.IS_MODULE] = True
                    self.loadModule(moduleName, dd, dictToCopyFrom)
                    if moduleName != dd[self.MODULE_NAME]:
                        self.loadModule(dd[self.MODULE_NAME], dd, dictToCopyFrom)
                    # source module found, replace variables and return it
                    m = self.loadModule(dd[self.MODULE_NAME], dd, dictToCopyFrom)
                    return m
            return self.loadModule(moduleName, {}, dictToCopyFrom)

        for key in d:
            # ignore parent key
            if key != self.PARENT:
                value = d[key]
                if key == moduleName:
                    # module found, replace variables and return it
                    return self.loadModule(moduleName, value, dictToCopyFrom)
                else:
                    if type(value) is dict:
                        if self.isModule(value):
                            # recursively find the module
                            m = self.findModule(moduleName, value)
                            if m is not None:
                                return m
        # not found
        return None

    def loadModule(self, moduleName, d, dictToCopyFrom):
        self.logMsgAlways("warning", ">>>loading module " + moduleName)

        moduleDict = self.modulesDict.get(moduleName)
        if moduleDict is None:
            # create empty module entry
            moduleDict = self.createModuleEntry(moduleName)
            moduleDict[self.IS_MODULE] = self.hasTerraform(d)

        if dictToCopyFrom is not None:
            mdv = moduleDict[self.VARIABLE]
            # add/replace the passed in variables to the module's variables
            for attr in dictToCopyFrom:
                if attr != self.SOURCE:
                    # only replace on pass #1 if resolved
                    if self.passNumber == 2 or self.isResolved(dictToCopyFrom[attr]):
                        mdv[attr] = dictToCopyFrom[attr]

        # load all attributes for this module
        self.loadModuleAttributes(moduleName, d, moduleDict, None)
        # resolve variables for this module
        self.resolveVariablesInModule(moduleName, moduleDict)
        return moduleDict

    def isResolved(self, var):
        if type(var) is str:
            return self.isStrResolved(var)
        elif type(var) is dict:
            for key in var:
                if not self.isResolved(var[key]):
                    return False
        elif type(var) is list:
            for value in var:
                if not self.isResolved(value):
                    return False
        else:
            return False
        return True

    def isStrResolved(self, var):
        for varErrorReplacement in self.variableErrorReplacement:
            if varErrorReplacement in var:
                return False
            
        return True

    def createModuleEntry(self, moduleName):
        self.modulesDict[moduleName] = {}
        moduleDict = self.modulesDict[moduleName]
        moduleDict[self.VARIABLE] = {}
        moduleDict[self.LOCALS] = {}
        moduleDict[self.OUTPUT] = {}
        moduleDict[self.RESOURCE] = {}
        moduleDict[self.IS_MODULE] = False
        return moduleDict

    def loadModuleAttributes(self, moduleName, d, moduleDict, tfDict):
        if self.isModule(d):
            if tfDict is None:
                tfDict = d
            else:
                # skip nested modules
                return

        for key in sorted(d):
            # ignore parent key
            if key != self.PARENT:
                value = d[key]
                if key == self.LOCALS:
                    # get values for all local variables
                    for local in value:
                        # only replace on first pass or not already fully resolved
                        if self.passNumber == 1 or self.containsVariable(moduleDict[self.LOCALS][local]):
                            moduleDict[self.LOCALS][local] = value[local]
                elif key == self.OUTPUT:
                    for output in value:
                        # only replace on first pass or not already fully resolved
                        if self.passNumber == 1 or self.containsVariable(moduleDict[self.OUTPUT][output]):
                            moduleDict[self.OUTPUT][output] = value[output][self.VALUE]
                elif key == self.RESOURCE:
                    if self.passNumber == 1:
                        for resourceType in value:
                            resourceNames = value[resourceType]
                            for resourceName in resourceNames:
                                config = resourceNames[resourceName]
                                moduleDict[self.RESOURCE][resourceName] = TerraformResource(resourceType, resourceName, config, d[self.FILE_NAME], moduleName)
                elif key == self.VARIABLE:
                    '''
                    value could be a string as in below case
                        condition {
                            test = "ArnEquals"
                            variable = "aws:SourceArn"
                            values = ["${var.services_entry_arn}"]
                        }
                    '''
                    if type(value) is dict:
                        # initialize any default values for variables
                        for variable in value:
                            if value[variable].get(self.DEFAULT) is not None:
                                moduleDict[self.VARIABLE][variable] = value[variable][self.DEFAULT]
                elif key == self.MODULE:
                    # loop through all modules
                    for mn in value:
                        # resolve parameter variables first
                        for parameter in value[mn]:
                            if parameter != self.SOURCE:
                                replacementValue = self.resolveVariableByType(value[mn][parameter], moduleName)
                                if replacementValue != value[mn][parameter]:
                                    self.logMsgAlways("warning", "replaced module " + mn + " parameter " + parameter + " value " + str(value[mn][parameter]) + " with " + str(replacementValue))
                                    value[mn][parameter] = replacementValue
                        # get defined module; load it if not already there
                        md = self.getModule(mn, False, value[mn], tfDict)
                        # copy all outputs from source module (md) to containing module variable
                        for output in md[self.OUTPUT]:
                            # only copy if not already there
                            if moduleDict[self.VARIABLE].get(output) is None:
                                moduleDict[self.VARIABLE][output] = md[self.OUTPUT][output]
                else:
                    if type(value) is dict:
                        # don't load any other nested modules
                        if not self.isModule(value):
                            self.loadModuleAttributes(moduleName, value, moduleDict, tfDict)

    def getSourcePath(self, parameterDict):
        for parameter in parameterDict:
            if parameter == self.SOURCE:
                return parameterDict[parameter]
        return None

    def getModuleDictFromSourcePath(self, sourcePath, d):
        # source is local
        while sourcePath != "":
            t = self.getNextLevel(sourcePath, "/")
            currentModule = t[0]
            sourcePath = t[1]
            if currentModule == "..":
                # move up a level
                d = d[self.PARENT]
            elif currentModule == ".":
                # current directory; do nothing
                pass
            else:
                # move down to currentModule level
                d = d.get(currentModule, False)
                if d is False:
                    return False
        return d

    # resolve variables (anything surrounded by ${}) in given moduleDict
    def resolveVariablesInModule(self, moduleName, moduleDict):
        self.shouldLogErrors = False
        # resolve variables
        for key in moduleDict[self.VARIABLE]:
            value = moduleDict[self.VARIABLE][key]
            replacementValue = self.resolveVariableByType(value, moduleName)
            moduleDict[self.VARIABLE][key] = replacementValue
            if replacementValue != value:
                self.logMsgAlways("warning", "replaced variable " + key + " value " + str(value) + " with " + str(replacementValue))
        # resolve locals
        for key in moduleDict[self.LOCALS]:
            value = moduleDict[self.LOCALS][key]
            replacementValue = self.resolveVariableByType(value, moduleName)
            moduleDict[self.LOCALS][key] = replacementValue
            if replacementValue != value:
                self.logMsgAlways("warning", "replaced local variable " + key + " value " + str(value) + " with " + str(replacementValue))
        # resolve outputs
        for key in moduleDict[self.OUTPUT]:
            value = moduleDict[self.OUTPUT][key]
            replacementValue = self.resolveVariableByType(value, moduleName)
            moduleDict[self.OUTPUT][key] = replacementValue
            if replacementValue != value:
                self.logMsgAlways("warning", "replaced output variable " + key + " value " + str(value) + " with " + str(replacementValue))
        # resolve resources
        self.shouldLogErrors = True
        for key in moduleDict[self.RESOURCE]:
            value = moduleDict[self.RESOURCE][key].config
            replacementValue = self.resolveVariableByType(value, moduleName)
            moduleDict[self.RESOURCE][key].config = replacementValue
            if replacementValue != value:
                self.logMsgAlways("warning", "replaced resource variable " + key + " value " + str(value) + " with " + str(replacementValue))

    def resolveVariableByType(self, value, moduleName):
        if type(value) is str:
            return self.resolveVariableLine(value, moduleName)
        elif type(value) is dict:
            return self.resolveDictVariable(value, moduleName)
        elif type(value) is list:
            return self.resolveListVariable(value, moduleName)
        else:
            return value

    def resolveDictVariable(self, value, moduleName):
        returnValue = {}
        for key in value:
            returnValue[key] = self.resolveVariableByType(value[key], moduleName)
        return returnValue

    def resolveListVariable(self, value, moduleName):
        index = 0
        for v in value:
            value[index] = self.resolveVariableByType(v, moduleName)
            index += 1
        return value

    # returns True if given dictionary d contains a key of __isModule__
    def isModule(self, d):
        for key in d:
            if key == self.IS_MODULE:
                return d[key]
        return False

    # returns True if given dictionary d contains at least one terraform file
    def hasTerraform(self, d):
        for key in d:
            if key.lower().endswith(self.TF):
                return True
        return False

    # resolve entire variable
    def resolveVariableLine(self, value, moduleName):
        if not self.containsVariable(value):
            return value
        # a variable needs to be replaced
        t = self.findVariable(value, True)
        var = t[0]
        b = t[1]
        e = t[2]
        if var.startswith("["):
            var = var[1:len(var)-1]            
        rv = self.resolveVariable(var, moduleName)
        if b == 0 and (e == len(value) or e == -1):
            # full replacement; don't merge since a string may not have been returned
            newValue = rv[0]
        else:
            newValue = value[:b] + str(rv[0]) + value[e:]
        # recursively resolve the variables since there may be more than one variable in this value
        return self.resolveVariableByType(newValue, moduleName)

    # resolve innermost variable
    def resolveVariable(self, value, moduleName, dictToCopyFrom=None, tfDict=None):
        # find variable (possibly in brackets)
        isOldTFvarStyle=False
        v, b, e, insideBrackets, foundDelineator, foundDelineatorErrRepl = self.findVariable(value, False)
        if len(v) > 1 and v[1] == "{":
            isOldTFvarStyle = True
        if not insideBrackets and isOldTFvarStyle:
            # inside ${}; remove them
            var = value[2:e-1]
        else:
            var = v
        # update moduleName in case we switch modules and need to recurse more
        replacementValue, moduleName, isHandledType = self.getReplacementValue(var, moduleName, isOldTFvarStyle, dictToCopyFrom, tfDict)
        if replacementValue == var:
            # couldn't find a replacement; change to our notation to mark it
            if isHandledType:
                self.logMsg("error", "Couldn't find a replacement for: " + self.getOrigVar(var) + " in " + moduleName)
            else:
                self.logMsg("debug", "Couldn't find a replacement for: " + self.getOrigVar(var) + " in " + moduleName)
            if not isOldTFvarStyle:
                # strip off replaceable variable
                var = var[len(foundDelineator):]
            replacementValue = value[:b] + foundDelineatorErrRepl + var
            if insideBrackets:
                replacementValue += "]"
            if not isOldTFvarStyle and len(value) > 1 and value[1] == "{":
                replacementValue += "}"
            if isOldTFvarStyle and e > 0:
                # remove closing brace
                replacementValue += value[e-1:]
            return (replacementValue, not insideBrackets)

        if type(replacementValue) is str:
            if insideBrackets:
                self.logMsgAlways("info", "  replacing [" + var + "] with " + replacementValue)
                # resolve the variable again since the replacement may also contain variables
                return (value[:b] + self.resolveVariableLine(replacementValue, moduleName) + value[e:], not insideBrackets)
            else:
                if v == replacementValue:
                    # this prevents a loop
                    replacementValue = replacementValue.replace(foundDelineator, foundDelineatorErrRepl, 1)
                    self.logMsg("debug", "Couldn't find a replacement for: " + self.getOrigVar(var) + " (would have looped) in " + moduleName)
                else:
                    self.logMsgAlways("info", "  replacing ${" + var + "} with " + replacementValue)
                    # resolve the variable again since the replacement may also contain variables
                    return (self.resolveVariableLine(replacementValue, moduleName), not insideBrackets)
        elif type(replacementValue) is int:
            self.logMsgAlways("info", "  replacing ${" + var + "} with " + str(replacementValue))
        elif type(replacementValue) is dict:
            bb = value.find("[")
            if bb == -1:
                # assume a dictionary is expected as replacement value
                if isOldTFvarStyle:
                    self.logMsgAlways("info", "  replacing ${" + value + "} with " + str(replacementValue))
                else:
                    self.logMsgAlways("info", "  replacing " + value + " with " + str(replacementValue))
                return (replacementValue, not insideBrackets)
            ee = value.find("]", bb)
            if ee == -1:
                self.add_error("Couldn't find ] for dictionary entry in replacement variable: " + value, moduleName, "---", "high")
                return (foundDelineatorErrRepl + value + "}", not insideBrackets)
            vn = value[bb+1:ee]
            if isOldTFvarStyle:
                replacementValue = replacementValue.get(vn, foundDelineatorErrRepl + value[len(foundDelineator):])
            else:
                replacementValue = replacementValue.get(vn, foundDelineatorErrRepl + value[len(foundDelineator):])
            if replacementValue is str and replacementValue.startswith(foundDelineatorErrRepl):
                self.logMsg("debug", "Couldn't find a replacement (2) for: " + self.getOrigVar(value) + " in " + moduleName)
            if type(replacementValue) is list:
                replacementValue = str(replacementValue)
                if isOldTFvarStyle:
                    self.logMsgAlways("info", "  replacing " + foundDelineator + value + "}[" + vn + "] with " + replacementValue)
                else:
                    self.logMsgAlways("info", "  replacing " + value + " with " + replacementValue)

        if type(replacementValue) is list:
            replacementValue = str(replacementValue)
            if isOldTFvarStyle:
                self.logMsgAlways("info", "  replacing " + foundDelineator + var + "} with " + replacementValue)
            else:
                self.logMsgAlways("info", "  replacing " + var + " with " + replacementValue)

        return (replacementValue, not insideBrackets)

    def getOrigVar(self, var):
        if var.startswith(self.vars[1]) or var.startswith(self.vars[2]):
            return self.vars[0] + var[len(self.vars[1]):]
        elif var.startswith(self.locals[1]) or var.startswith(self.locals[2]):
            return self.locals[0] + var[len(self.locals[1]):]
        elif var.startswith(self.modules[1]) or var.startswith(self.modules[2]):
            return self.modules[0] + var[len(self.modules[1]):]
        else:
            return var

    # check if given value contains a variable anywhere
    def containsVariable(self, value):
        t = self.containsVariableByType(value)
        if t[0] != -1:
            return True
        return False

    def containsVariableByType(self, value):
        if type(value) is str:
            return self.findVariableDelineatorsForVars(value, False)
        elif type(value) is dict:
            return self.containsVariableDict(value)
        elif type(value) is list:
            return self.containsVariableList(value)
        else:
            # not a variable
            return (-1, 0)

    def containsVariableDict(self, value):
        returnValue = {}
        for key in value:
            returnValue[key] = self.containsVariableByType(value[key])
        # check all returned values
        for key in returnValue:
            if returnValue[key][0] != -1:
                # variable found
                return (1, 0)
        # no variables found
        return (-1, 0)

    def containsVariableList(self, value):
        index = 0
        for v in value:
            value[index] = self.containsVariableByType(v)
            index += 1
        # check all returned values
        for v in value:
            if v[0] != -1:
                # variable found
                return (1, 0)
        # no variables found
        return (-1, 0)

    # find deepest nested variable in given value
    def findVariable(self, value, isNested, previouslyFoundVar=None):
        # pass 1: if unreplaceable, change $ to @
        # pass 2: if unreplaceable, change both $ & @ to !
        if type(value) is str:
            isVar = False
            val = value
            if previouslyFoundVar:
                insideBrackets = previouslyFoundVar[3]
            else:
                insideBrackets = False
            if isNested and type(previouslyFoundVar) is str and "{" in previouslyFoundVar[0]:
                # if this is a nested call and the outer call found ${, only look for the brace now
                braceOnly = True
            else:
                braceOnly = False
 
            b, e, foundDelineator, foundDelineatorErrRepl = self.findVariableDelineatorsForVars(val, braceOnly)
            if b == -1:
                return None                
            if b > 0:
                partial = value[:b]
                if partial[len(partial)-1] == "[":
                    # open bracket found before the variable
                    insideBrackets = True
                    partial = value[b:e]
                    if partial[len(partial)-1] == "]":
                        # close bracket found after the variable, remove from variable end
                        e -= 1
                
            isVar = True
            if "{" in foundDelineator:
                if e == -1:
                    # problem
                    self.add_error("Matching close brace not found: " + value, "---", "---", "high")
                    return None
                foundVar = (value[b:e], b, e, insideBrackets, foundDelineator, foundDelineatorErrRepl)
            else:
                foundVar = (value[b:e], b, e, insideBrackets, foundDelineator, foundDelineatorErrRepl)
            
            newSearchValue = foundVar[0]
            if isVar:
                # remove delineator(s)
                if newSearchValue.endswith("}"):
                    newSearchValue = newSearchValue[2:len(newSearchValue)-1]
                else:
                    newSearchValue = newSearchValue[len(foundDelineator):]
            else:
                newSearchValue = newSearchValue[1:len(newSearchValue)-1]
                if not insideBrackets:
                    # adjust beginning & ending since nested inside previouslyFoundVar
                    fv_length = len(previouslyFoundVar[4])
                    b += fv_length
                    e += fv_length
                foundVar = (newSearchValue, b, e, insideBrackets, foundDelineator, foundDelineatorErrRepl)
            if newSearchValue not in self.terraform_workspaces[0]:
                # recursively find variable
                fv = self.findVariable(newSearchValue, True, foundVar)
                if fv is None:
                    # no variable found
                    return foundVar
                if foundVar[0].endswith("}") and fv[1] == 0 and fv[2] == len(newSearchValue):
                    # return originally found variable which is the old style
                    return foundVar
                if insideBrackets:
                    # use beginning & ending from previous
                    fv = (fv[0], b, e, fv[3], fv[4], fv[5])
                return fv
            else:
                return foundVar
        return previouslyFoundVar

    def findVariableDelineatorsForVars(self, value, braceOnly):
        if braceOnly and value not in self.terraform_workspaces:
            b, e = self.findVariableDelineators(value, self.variableFind[0], "}", self.variableErrorReplacement[0])
            if b > -1:
                return b, e, self.variableFind[0], self.variableErrorReplacement[0]
        else:
            prevB = -1
            for varPrefix, varErrorReplacement in zip(self.variableFind, self.variableErrorReplacement):
                if varPrefix[1] == "{":
                    closeVar = "}"
                else:
                    closeVar = None
                b, e = self.findVariableDelineators(value, varPrefix, closeVar, varErrorReplacement)
                if b > -1:
                    if closeVar != None or b == 0 or (value[b-1] != "{"):
                        if b > prevB:
                            prevB = b;
                            prevE = e
                            prevVarPrefix = varPrefix
                            prevVarErrorReplacement = varErrorReplacement
            if prevB != -1:
                return prevB, prevE, prevVarPrefix, prevVarErrorReplacement
        return -1, 0, None, None

    def findVariableDelineators(self, value, openVar, closeVar, varErrorReplacement=None):
        '''
        This is valid:  name-prefix = "sf-${module.common.account_name}-${local.pcas_vpc_type}-${local.env}-${module.common.region}"
        This is not:    name-prefix = "sf-module.common.account_name-local.pcas_vpc_type-local.env-module.common.region"
        i.e. if combining variables into one variable, must use old ${} variable style
        '''
        b = value.rfind(openVar)
        if b == -1:
            return -1, 0
        if openVar == "[":
            # check if preceeded by :
            matchObject = self.REGEX_COLON_BRACKET.search(value)
            if matchObject != None:
                return -1, 0
        if closeVar == None:
            # search for default "closeVars"
            defaultCloseVars = [",", ")", "}"]
            prevE = 99999
            for closeVar in defaultCloseVars:
                e = value.find(closeVar, b)
                if e != -1 and e < prevE:
                    prevE = e
            if prevE != 99999:
                return b, prevE
            # no close value found, use length of value
            return b, len(value)
        v = value[b+1:]
        nested = 0
        for index, char in enumerate(v):
            if char == closeVar:
                if nested == 0:
                    return b, b+index+2
                # just closed a nested variable
                nested -= 1
            if v[index:index+len(openVar)] == openVar or (varErrorReplacement != None and len(v) >= index+len(varErrorReplacement) and v[index:index+len(varErrorReplacement)] == varErrorReplacement):
                # start of a nested variable
                nested += 1
        # error: matching closeVar not found
        return 0, -1

    # find replacement value for given var in given moduleName
    def getReplacementValue(self, var, moduleName, isOldTFvarStyle, dictToCopyFrom=None, tfDict=None):
        replacementValue = None
        if var.startswith('"') and var.endswith('"'):
            return var[1:len(var)-1], moduleName, True
        subscript = None
        b = var.find("[")
        if b != -1:
            v = var[:b]
            e = var.find("]", b)
            if e != -1:
                subscript = var[b+1:e]
                v += var[e+1:]
                if subscript[0] == '"' or subscript[0] == "'":
                    # remove quotes
                    subscript = subscript[1:len(subscript)-1]
        else:
            v = var

        isHandledType = False
        notHandled = ["?", "==", "!=", ">", "<", ">=", "<=", "&&", "||", "!", "+", "-", "*", "/", "%"]
        moduleDict = self.modulesDict[moduleName]
        if isOldTFvarStyle:
            varIndex = 0
        else:
            varIndex = self.passNumber - 1
        if var.startswith(self.vars[varIndex]):
            # conditional statements, boolean statements, and math are not currently handled
            if not any(x in var for x in notHandled):
                isHandledType = True
            v = v[len(self.vars[varIndex]):]
            index = v.find('.')
            if index > -1:
                subscript = v[index+1:]
                v = v[:index]
            replacementValue = moduleDict[self.VARIABLE].get(v)
        elif var.startswith(self.locals[varIndex]):
            if not any(x in var for x in notHandled):
                isHandledType = True
            v = v[len(self.locals[varIndex]):]
            replacementValue = moduleDict[self.LOCALS].get(v)
        elif var.startswith(self.modules[varIndex]):
            if not any(x in var for x in notHandled):
                isHandledType = True
            # variable is in a different module
            modulePrefixLength = len(self.modules[varIndex])
            e = v.find(".", modulePrefixLength)
            if e == -1:
                self.add_error("Error Resolving module variable: " + var + "  expected ending '.' not found", moduleName, "---", "high")
            else:
                moduleName = v[modulePrefixLength:e]
                md = self.getModule(moduleName, True, dictToCopyFrom, tfDict)
                moduleOutputDict = md[self.OUTPUT]
                e += 1
                remainingVar = v[e:]
                while remainingVar != "":
                    t = self.getNextLevel(remainingVar, ".")
                    moduleOutputDict = moduleOutputDict.get(t[0])
                    if moduleOutputDict is None:
                        self.logMsg("error", "Error resolving variable: " + v + "  variable not found in module (no module source available?) in " + moduleName)
                        return var, moduleName, True
                    remainingVar = t[1]
                if type(moduleOutputDict) is dict:
                    replacementValue = moduleOutputDict.get(self.VALUE, moduleOutputDict)
                else:
                    replacementValue = moduleOutputDict
        elif var == self.terraform_workspaces[varIndex]:
            isHandledType = True

        if type(replacementValue) is dict:
            if len(replacementValue) == 0:
                replacementValue = None
            elif subscript != None:
                replacementValue = replacementValue[subscript]

        if replacementValue is None:
            replacementValue = self.variablesFromCommandLine.get(var, var)

        return replacementValue, moduleName, isHandledType

    def getPreviousLevel(self, var, separator):
        b = var.rfind(separator)
        if b == -1:
            b = len(var)
        return (var[:b], var[b+1:])

    def getNextLevel(self, var, separator):
        b = var.find(separator)
        if b == -1:
            b = len(var)
        return (var[:b], var[b+1:])

    # add given failure in given fileName
    def add_failure(self, failure, moduleName, fileName, severity):
        self.jsonOutput["failures"].append( self.getFailureMsg(severity, failure, moduleName, fileName) )

    # add given error in given fileName
    def add_error(self, error, moduleName, fileName, severity):
        if self.passNumber == 2 and self.shouldLogErrors:
            self.add_error_force(error, moduleName, fileName, severity)

    def add_error_force(self, error, moduleName, fileName, severity):
        self.jsonOutput["errors"].append( self.getFailureMsg(severity, error, moduleName, fileName) )

    def getFailureMsg(self, severity, msg, moduleName, fileName):
        message = {}
        message["severity"] = severity
        message["message"] = msg
        message["moduleName"] = moduleName
        message["fileName"] = fileName
        return message

    def logMsg(self, type, msg):
        if self.passNumber == 2:
            self.logMsgAlways(type, msg)

    def logMsgAlways(self, type, msg):
        if type == "error":
            logging.error(msg)
        elif type == "warning":
            logging.warning(msg)
        elif type == "info":
            logging.info(msg)
        elif type == "debug":
            logging.debug(msg)
