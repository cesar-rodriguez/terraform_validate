# Terraform Validate

Linux: [![Linux Build Status](https://travis-ci.org/elmundio87/terraform_validate.svg?branch=master)](https://travis-ci.org/elmundio87/terraform_validate)

Windows: [![Windows Build status](https://ci.appveyor.com/api/projects/status/36dwtekc8tvrny24/branch/master?svg=true)](https://ci.appveyor.com/project/elmundio87/terraform-validate/branch/master)

A python package that allows users to define Policy as Code for Terraform configurations. 

By parsing a directory of .tf files using `pyhcl`, each defined resource can be tested using this module. 

## Updates in this fork

### Meant to be used with my fork of terrascan

### Modules are resolved and variables are replaced**

* if variables are defined outside the scope of the Terraform files, like in AWS, they are not replaced
* modules sourced outside the scope of the Terraform files, like in AWS or git, are not handled
* terraform functions are not handled; i.e. split(",",local.s3_logging_arns)
* equations are not handled; i.e. var.s3\_logging\_arns == "" ? "arn:aws:s3:::DISABLED/" : var.s3\_logging_arns
* does not process anything inside any HEREDOCs.  However, this can be fixed by adding the following lines of code to lexer.py in the \_end_heredoc function which is part of the pyhcl open source project:

```
            # load value as json
            try:
                t.value = json.loads(t.value)
            except:
                pass
```

### Does not raise any exceptions

* stores all failures and writes them out at the end
* all failures include the problem module and file name

### Various levels of logging allowed

* The logging level can be changed by passing the -c or --config parameter with one of the logging levels listed below.  There are five logging options available.  All are written to the console only.
  * none:  no logging
  * error: only shows errors (default); i.e. couldn't find module or couldn't replace a variable when expected to be handled
  * warning: also shows every module being loaded and every variable being replaced
  * info: also shows intermediate variable replacement
  * debug: also shows when a variable couldn't be replaced even if not expected to be handled and the files that were processed



## Example Usage

### Check that all AWS EBS volumes are encrypted


```
import terraform_validate

jsonOutput = {
        "failures": [],
        "errors": []
    }

class Rules(unittest.TestCase):

    def setUp(self):
        self.v = terraform_validate.Validator()
        self.v.preprocessor = self.preprocessor
        
    def test_aws_ebs_volume_encryption(self):
        # verify that all resources of type 'aws_ebs_volume' are encrypted
        self.v.error_if_property_missing() # Fail any tests if the property does not exist on a resource
        # run rule on all terraform files individually
        validator_generator = self.v.get_terraform_files()
        for validator in validator_generator:        
            # to change severity, override it here (default is high)
            validator.severity = "high"        
            validator.resources('aws_ebs_volume').property('encrypted').should_equal(True)



resource "aws_ebs_volume" "foo" {
  # This would fail the test
  encrypted = false
}
```

## Behaviour functions

These affect the results of the Validation functions in a way that may be required for your tests.

### Validator.error_if_property_missing()

By default, no errors will be raised if a property value is missing on a resource. This changes the behavior of .property() calls to raise an error if a property is not found on a resource.

### Validator.severity

The severity is only displayed in the failure message.  By default, the severity is set to "high".  To change the severity for a rule to medium, set Validator.severity = "medium".

## Search functions

These are used to gather property values together so that they can be validated.

### Validator.resources([resource_types])
Searches for all resources of the required types and outputs a `TerraformResourceList`.

Can be chained with a `.property()` function.

If passed a string as an argument, search through all resource types and list the ones that match the string as a regex.
If passed a list as an argument, only use the types that are inside the list.

Outputs: `TerraformResourceList`

### TerraformResourceList.property(property_name)

Collects all top-level properties in a `TerraformResourceList`  and exposes methods that can be used to validate the property values.

Can be chained with another `.property()` call to fetch nested properties.

eg. ``.resource('aws_instance').property('name')``

### TerraformResourceList.find_property(regex)

Similar to `TerraformResourceList.property()`, except that it will attempt to use a regex string to search for the property.

eg. ``.resource('aws_instance').find_property('tag[a-z]')``


### TerraformPropertyList.property(property_name)

Collects all nested properties in `TerraformPropertyList` and exposes methods that can be used to validate the property values.

eg. ``.resource('aws_instance').property('tags').property('name')``


### TerraformPropertyList.find_property(regex)

Similar to `TerraformPropertyList.property()`, except that it will attempt to use a regex string to search for the property.

eg. ``.resource('aws_instance').find_property('tag[a-z]')``

## Validation functions

If there are any failures/errors, these functions will store the failures/errors. The purpose of these functions is to validate the property values of different resources.

### TerraformResourceList.should_have_properties([required_properties])

Will verify that all of the properties in `required_properties` are in a `TerraformResourceList`.

### TerraformResourceList.should_not_have_properties([excluded_properties])

Will verify that none of the properties in `excluded_properties` are in a `TerraformResourceList`.

### TerraformResourceList.name_should_match_regex(regex)

Will verify that the Terraform resource name matches the value of `regex`

### TerraformResourceList.should_not_exist()

Will verify that the resources in `TerraformResourceList` do not exist

### TerraformPropertyList.should_have_properties([required_properties])

Will verify that all of the properties in `required_properties` are in a `TerraformPropertyList`.

### TerraformPropertyList.should_not_have_properties([excluded_properties])

Will verify that none of the properties in `excluded_properties` are in a `TerraformPropertyList`.

### TerraformPropertyList.should_equal(expected_value)

Will verify that the value of the property is equal to `expected_value`

### TerraformPropertyList.should_equal_case_insensitive(expected_value)

Will verify that the value of the property is equal to `expected_value` case insensitive

### TerraformPropertyList.should_not_equal(unexpected_value)

Will verify that the value of the property does not equal `unexpected_value`

### TerraformPropertyList.should_not_equal_case_insensitive(unexpected_value)

Will verify that the value of the property does not equal `unexpected_value` case insensitive

### TerraformPropertyList.should_match_regex(regex)

Will verify that the value of the property matches the value of `regex`

### TerraformPropertyList.list_should_contain([value])

Will verify that the list value contains all of the `[value]`

### TerraformPropertyList.list_should_not_contain([value])

Will verify that the list value does not contain any of the `[value]`

