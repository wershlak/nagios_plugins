# Nagios Plugins

Creating a repo for some nagios plugins I've done.

## Installation

copy scripts into nagios plugin directory


## Usage

Create a command definition

        # 'check_cisco_stack' command definition
        define command{
             command_name    check_cisco_stack
             command_line    $USER1$/check_cisco_stack.py -H $HOSTADDRESS$ $ARG1$
        }

Define a service for the stack

        define service{
          use   generic-service   ; Inherit default values from a template
          servicegroups   <group name> ;
          host_name <stack hostname>
          service_description Cisco Stack
          check_command check_cisco_stack! -H <ip address> -c <community>
        }

## Contributing

Bug reports and pull requests are welcome on GitHub at https://github.com/wershlak/nagios_plugins.

## License

The gem is available as open source under the terms of the [MIT License](http://opensource.org/licenses/MIT).
