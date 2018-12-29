# Custom components for Home Assistant
## Sony ADCP Switch Component

A component for Home Assistant that makes a Sony ADCP (Advanced Display Control Protocol) compliant projector or display. This was based off of the official 'telnet switch', and is still work in progress.

Currently it does
* Polls display/projector if it is running or not (on/off)
* Acts as an on/off switch so that you can turn it on or off, while keeping state correct (unlike remote emulation)
* Supports authentication

Still very much alpha, but works fine if all you want is the above functionality. I have a lot of ideas on how to improve upon this, but hopefully the code will give a good baseline for those who want to get started with controlling their Sony displays through ADCP protocol. 

#### Configuration variables:
**resource** (String) (Required): Host name or IP address of the device.<br />
**port** (integer)(Optional): Port to connect to.<br />Default value: 23.<br />
**command_on** (string)(Required): Command to turn device on. <br /> Should probably be ```"power \"on\""```<br />
**command_off** (string)(Required): Command to turn device off. <br /> Should probably be ```"power \"off\""```<br />
**command_state** (string)(Optional): The command to verify status. How this is interpreted depends on ```value_template``` below. Example configuration assumes that this should return ```standby``` when off, anything else means that display is still running. This will make device state ```on``` when cooling down etc. <br /> Should probably be ```"{{ value != '\"standby\"' }}"```<br />
**timeout** (string) (Optional): The name used to display the switch in the frontend.<br />
  
#### Example:
```
switch:
  - platform: SONY_ADCP
    switches:
      projector:
      resource: 192.168.1.140
      port: 53595
      command_on: "power \"on\""
      command_off: "power \"off\""
      command_state: "power_status ?"
      value_template: "{{ value != '\"standby\"' }}"
```

#### Quirks, gotchas, helpful hints and todo:

* Currently password is hardcoded variable in component. Will clean up and use secrets.yaml at some point.
* Defaults are still based on telnet.switch, so should be cleaned up to default to ADCP protocol. Currently you have to specify the commands as per the example to follow protocol.
* Polling is kind of inefficient as ADCP is couple with ADAP (Advanced Display Announcement Protocol), where display automatically announces power state over UDP every 30 seconds. This component currently polls over TCP every 10 seconds. Not a big deal, but could potentially be used for nicer integration into Home Assistant and automatic setup, assuming authentication is turned off.
* If you have problems and want to see responses in the log, turn on ```debug``` level with logger, and you should get necessary server reponses to troubleshoot.
* I statically mapped the IP for my projector in my DHCP server, if you don't want to do that, you can set static IP and other network settings, passwords etc through a web interface (or at least I could on my Sony VPL-VW535). You can set IP white-list per protocol, set port per protocol etc. Check the manual for your particular model.
* ADCP is a very simple, and unencrypted, protocol. [Wireshark](https://www.wireshark.org/) is very useful if you want to see what is going on if you are having problems. This is how I validated my understanding of the ADAP protocol.

#### Notes on ADAP and ADCP:

Here are some notes on documents used to figure out ADAP/ADCP protocol, authentication, command codes etc. I personally used telnet and quick python hacks to check responses from my Sony VPL-VW535. Currently ADAP, which is an announcment UDP protocol, is not used in this component. For ADCP, which is the TCP based control protocol, I used page 12 in the [Sony Data Projector Protocol Manual (Common)](https://pro.sony/s3/2018/07/05125823/Sony_Protocol-Manual_1st-Edition.pdf). This component automatically handles both authentication and no-password scenarios automatically.
Authentication and basic function currently supported is common functionality that is supported on all ADCP devices, as described in the manual above. However, for more advanced control functionality you need to get a hold of the [Sony Data Projector Protocol (Supported Command List)](https://pro.sony/s3/cms-static-content/uploadfile/26/1237493982326.pdf) for your device. If you want to expand functionality and do more advanced controls start by going through this, testing on telnet manually, and then tweaking this component to your needs. Contributions and forks more than welcome! :D
