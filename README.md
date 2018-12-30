# Custom components for Home Assistant
## Sony ADCP Switch Component

A component for Home Assistant that makes a Sony ADCP (Advanced Display Control Protocol) compliant projector or display into a switch. This was based off of the official 'telnet switch', and is still work in progress.

Currently it:
* Polls display/projector if it is running or not (on/off)
* Acts as an on/off switch so that you can turn it on or off, while keeping state correct (unlike remote emulation)
* Supports authentication

Still very much a work in progress, but works fine if all you want is the above functionality. I have a lot of ideas on how to improve upon this, but hopefully the code will give a good baseline for those who want to get started with controlling their Sony displays through ADCP protocol. 

### Configuration

This component follows ADCP standards, and the only thing you need to get it running should be to add the following in your config:

#### Basic Example with authentication turned off
```
switch:
  - platform: SONY_ADCP
    switches:
      projector:
       resource: 192.168.1.140
```

If you have authentication (passwords) set for your display/projector, you simply add, where ```MyPassword``` is what you have set in the projector setup screen for root/admin:

```
switch:
  - platform: SONY_ADCP
    switches:
      projector:
       resource: 192.168.1.140
       password: MyPassword
```


#### Configuration variables:
**resource** (String) (Required): Host name or IP address of the device.<br />
**port** (integer)(Optional): Port to connect to.<br />Default value: ```53595```<br />
**password** (string)(Optional): Password for the projector. Only needed if authentication is turned on in the projector. <br />
**name** (string)(Optional): User friendly name. <br /> Default: ```'Projector'```<br />
**command_on** (string)(optional): Command to turn device on. <br /> Default value: ```"power \"on\""```<br />
**command_off** (string)(optional): Command to turn device off. <br /> Default value: ```"power \"off\""```<br />
**command_state** (string)(Optional): The command to verify status. How this is interpreted depends on ```value_template``` below. Default configuration assumes that this should return ```standby``` when off, anything else means that display is still running. This will make device state ```on``` when cooling down etc. <br /> Default value: ```"power_status ?"```<br />
**value_template** (string)(Optional): The template used to verify projector state. The default value will consider projector running whenever value is anything BUT "standby". This optional configuration is left to make it easy to customize. For projectors that have periods of when lamp is cooling down, different people might want to consider this on/off depending on their preference. Refer to [Home Assistant template docs](https://www.home-assistant.io/docs/configuration/templating/) for usage.<br />Default value: ```"{{ value != '\"standby\"' }}"```<br />
  
#### Advanced Example:
Here is an example of what a configuration would look like with authentication set, projector running on a non-standard port, and to define that switch is only on when projector reports ```on```, considering it to be off when warming up, cooling down etc. Also, we will give it a more user friendly name.
```
switch:
  - platform: SONY_ADCP
    switches:
      projector:
       resource: 192.168.1.140
       name: "Living room projector"
       password: MyPassword
       port: 53500
       value_template: "{{ value == '\"on\"' }}"
```

### Quirks, gotchas, helpful hints and todo:

* ~Currently password is hardcoded variable in component. Will clean up and use secrets.yaml at some point.~
* ~Defaults are still based on telnet.switch, so should be cleaned up to default to ADCP protocol. Currently you have to specify the commands as per the example to follow protocol.~
* Polling is kind of inefficient as ADCP is coupled with ADAP (Advanced Display Announcement Protocol), where display automatically announces power state over UDP broadcast every 30 seconds. This component currently polls over ADCP TCP every 10 seconds. Not a big deal, but could potentially be used for nicer integration into Home Assistant and automatic setup, assuming authentication is turned off.
* If you have problems and want to see detailed responses in the log for troubleshooting, turn on ```debug``` level with logger, and you should get necessary server reponses to troubleshoot. In general I have tried to add warnings, errors and debug logs where it makes sense.
* I statically mapped the IP for my projector in my DHCP server, if you don't want to do that, you can set static IP and other network settings, passwords etc through a web interface (or at least I could on my Sony VPL-VW535). You can set IP white-list per protocol, set port per protocol etc. Check the manual for your particular model.
* ADCP is a very simple, and unencrypted, protocol. [Wireshark](https://www.wireshark.org/) is very useful if you want to see what is going on if you are having problems. This is how I validated my understanding of the ADAP protocol. If you just want to verify what your projector can, and cannot do, I recommend telnet'ing in and playing around first.

### Useful documents

* [Sony Data Projector Protocol Manual (Common)](https://pro.sony/s3/2018/07/05125823/Sony_Protocol-Manual_1st-Edition.pdf)</br>
The common part of the Sony Data Projector Protocol manual specifies the protocols (ADAP and ADCP), and provides commands that are common between different projector models. This is a good starting point if you want to understand how authentication works, and very basic use cases.
* [Sony Data Projector Protocol (Supported Command List) 1st edition](https://pro.sony/s3/cms-static-content/uploadfile/26/1237493982326.pdf)
For command lists and specifications for your specific projector model, you need to find a "Supported Command List" document for your particular projector. This one is for VPL-FZ60 and VPL-FH60 series. Models may be called other things but have functionality in different regions.
basic use cases.
* [Sony Data Projector Protocol (Supported Command List) 1st edition (Revised 5)](https://us.v-cdn.net/6031006/uploads/vbulletin_attachments/1/3/7/4/2813.pdf)
Here is a newer revision (revised 5) that has a larger set of supported projectors. This one has details on VPL-VW5000, VPL-VW760ES, VPL-VW675ES, VPL-VW665ES, VPL-VW365ES, VPL-VW260ES, VPL-VWVZ1000, VPL-VW65ES, VPL-VW45ES.</br>
I have a VPL-VW535, which is a Japan specific model, but in functionality and protocol is almost identical to VPL-VW675ES. If your projector supports ADCP, this component will support all basic functionality.
