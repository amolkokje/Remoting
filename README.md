# Remoting 
This project has been created to be able to assist remoting to Winows and Linux machines. 
The code base needs to run on windows machine as it uses windows utils like powershell, command line, psexec in the background to to Windows machine remoting tass.
For Linux machine remoting, it uses SSH and SFTP.

### Pre-Reqs:
Need following installed on controller host or machine you are running this automation from:
- [Powershell](https://docs.microsoft.com/en-us/powershell/scripting/setup/installing-windows-powershell?view=powershell-5.1)
- [PsExec]
  Note: Also need to provide PsExec.exe path in the WindowsRemoteMachine constructor if its not in Env path
