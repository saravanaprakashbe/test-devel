#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 08 15:37:20 2017
@module name: ibm_patch
@module type: Ansible module
@desc: Custom Ansible module for IBM WebSphere product suite end to end automated patching
@team: Architects
@author: Saravanaprakash Thangavel
@version: 1.0.0 """

ANSIBLE_METADATA = {'status': ['stable_version'],
                    'supported_by': 'core',
                    'version': '2.1.0.0'}
                    
DOCUMENTATION = """
module: ibm_patch
version_added: "1.0.0"
short_description: Install/Rollback the IBM WebSphere product suite patches
description:
    - Custom Ansible module for IBM WebSphere product suite end to end automated patching
options:
    state:
        required: false
        default: present
        choice: [present, absent]
        description:
            - Whether IBM WebSphere product suite fixes should be installed, or Rollback
            - present - Install, absent - Rollback
    fixid:
        required: True        
        descrption:
            - IBM WebSphere Product suite fixpack/ifix id
    kill:
        required: false
        default: False
        choices=[True, False]
        type: Boolean
        description:
            - If kill is True, then It will kill all the WebSphere related process forcefully
            - If kill is default='False'. then it will skip the host from patching. manually stop the processes and retry again.     
    path:
        required: True
        descrption:
            - IBM WebSphere product suite installed directory
    bkpath:
        required: false
        default: /IBM/websphere/dumps/backup
        descrption:
            - Path to backup the Profile and configuration
        
    iimpath:
        required: false
        default: /IBM/websphere/iim
        descrption:
            - IIM installed path
    repo:
        required: True        
        description:
            - path to patch/<fix name/fixpack version>/repository.config
            
"""

#Module Imports
import os
import re
import time
import datetime
import platform
import subprocess
import signal

#from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule


class ibm_patch():
    module = None
    module_facts = dict(
            installed = False,
            product = None,
            version = None,
            fixid = None,
            fixtype = None,
            installed_version = [],
            path = None,
            name = None,
            os_name = None,
            os_arch = None,
            os_kernal = None,            
            hostname = None,
            os_version = None,
            os_flavour = None,
            backup_status = 'NOT DONE',
            running_processes = {},
            #check_stdout = None,
            #check_stderr = None
    )
    

    def __init__(self):
        self.module = AnsibleModule(
                argument_spec = dict(
                    state           = dict(required=False, default='present', choices=['present', 'absent'], type='str'),
                    fixid           = dict(required=True, type='str'),
                    kill            = dict(required=False, default=False, choices=[True, False], type='bool'),
                    path            = dict(required=True, type='str'),                                  
                    bkpath         = dict(required=False, default='/IBM/websphere/dumps/backup', type='str'),
                    iimpath         = dict(required=False, default='/IBM/websphere/iim', type='str'),                                   
                    repo            = dict(required=True, type='str')
                ),
                supports_check_mode = True
        )
    
    
    def _fix_pattern(self):
        return {"WAS":{"FixPack":"websphere.ND", "iFix":"WS-WAS-"}, \
        "IHS":{"FixPack":"websphere.IHS", "iFix":"WS-WASIHS-"}, \
        "PLUGIN":{"FixPack":"websphere.PLG", "iFix":"WS-WASPlugIn"}}  
    
    def indexOf(self, string, delm, pos):
        return string.split(delm)[pos]
        
    
    def lastIndexOf(self, string, delm, pos): 
        return string.rsplit(delm, 1)[pos]
        
    
    def strip(self, string):
        return re.compile(r"\s+").sub("", string)
        
        
    def _check_path_exists(self, fnp) :
        return os.path.exists(fnp) 
           
        
    def createDir(self, dir, mod):
        if not os.path.exists(dir):
            os.makedirs(dir, mode=mod)
            
            
    def _check_dir_empty(self, dp):
        if os.path.exists(dp) and os.listdir(dp) != []:
            return False
        return True
        
        
    def _check_provisioned(self, packId, dp):
        if not os.path.exists(dp):
            return False
        return True


    def _check_empty_vars(self, var):
        #var = self.strip(var)
        if(var == None):
            NoneType = type(None)
            return type(var) == NoneType
        elif(var == ""):
            NoneType = type("")
            return type(var) == NoneType
        elif(var.lower() == "null"):
            NoneType = type('null')
            return type(var) == NoneType
        else:
            return False
     
    def _get_running_processes(self, _str_fltr):       
        _os_get_proc = None
        proc = None
        if self._check_os_name() and int(self.module_facts['os_version'].split('.')[0]) == 6:
            _os_get_proc = "pgrep -fl"
        elif self._check_os_name() and int(self.module_facts['os_version'].split('.')[0]) == 7:
            _os_get_proc = "pgrep -a"
        else:
            self.module.fail_json(
                        msg = "This ansible module is compatible only with RHEL 6.x & 7.x",
                        changed=False
            )
        proc = subprocess.Popen(
            ["{0} java | grep {1}".format(_os_get_proc, _str_fltr)],
             shell=True,
             stdout=subprocess.PIPE,
             stderr=subprocess.PIPE
        )
        val, err = proc.communicate()
        return val.splitlines()


    def _map_proc_to_pid(self, proc_list):
        running_proc = {}
        if proc_list:
            for proc in proc_list:
                if "java | grep" not in proc:
                    running_proc[proc.split()[-1]] = proc.split()[0]
        return running_proc        
        
   
    def _check_pid_exists(self, pid):
        try:
            os.kill(int(pid), 0)
        except OSError:
            return False
        else:
            return True  
    
    def _get_os_facts(self):
        _os_name = platform.linux_distribution()
        self.module_facts['os_name'] = _os_name[0]
        self.module_facts['os_version'] = _os_name[1]
        self.module_facts['os_flavour'] = _os_name[2]
        self.module_facts['os_arch'] = platform.architecture()[0]
        self.module_facts['os_kernal'] = platform.uname()[2]
        self.module_facts['hostname'] = platform.node()
        
        
            
    def _check_os_name(self):        
        if self.module_facts['os_name'].startswith("Red Hat"):
            return True
        return False

  

    def _map_fix_types(self, fix_id):        
        if "IFPI" in fix_id:
            self.module_facts['fixtype'] = "iFix"            
            if "-WS-WASIHS-" in fix_id:
                self.module_facts['product'] = "IHS"                            
            elif "-WS-WAS-" in fix_id:
                self.module_facts['product'] = "WAS"
            elif "-WS-WASPlugIn" in fix_id:
                self.module_facts['product'] = "PLUGIN"
            else:
                self.module_facts['product'] = None
        elif ".websphere." in fix_id:
            self.module_facts['fixtype'] = "FixPack"
            if ".websphere.ND." in fix_id:
                self.module_facts['product'] = "WAS"
            elif ".websphere.IHS." in fix_id:
                self.module_facts['product'] = "IHS"
            elif ".websphere.PLG." in fix_id:
                self.module_facts['product'] = "PLUGIN"
            else:
                self.module_facts['product'] = None
        else:
            self.module_facts['fixtype'] = None
        

    def _fixpack_version(self, version):
        return version[version.find("0")+1:].lstrip("0")
        
    
    def _base_version(self, f_pat, fix_id):
        if f_pat in fix_id:
            version = ".".join([str(x) for x in re.split('_|\.', fix_id) if x.isdigit()][:-2])        
            return "{0}.{1}".format(version[:version.find("0")], self._fixpack_version(version))
        
            
    def backup_configuration(self, p_name, path, b_path):
        b_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.createDir(b_path, 0755)
        if "WAS" in p_name:
            _prof_commmand = "{0}/bin/manageprofiles.sh  -listProfiles ".format(path)
            _get_profile = self.exec_command(_prof_commmand)
            prof_val, prof_err = _get_profile.communicate()
            if _get_profile.returncode != 0:
                self.module.fail_json(
                            msg="Get profile command failed on host {0}".format(self.module_facts['hostname']),
                            stderr=prof_err,
                            changed=False
                )
            for prof_name in re.sub('[\[\]\,]', ' ', prof_val).split():
                _bkp_command = "{0}/bin/manageprofiles.sh -backupProfile -profileName {1} \
                                -backupFile {2}/{3}_{4}_Backup_{5}_{6}.zip".format(path, prof_name, b_path, p_name, prof_name, self.module_facts['hostname'], b_time)
                _backup = self.exec_command(_bkp_command)
                out, err = _backup.communicate()            
                if _backup.returncode != 0:
                    self.module.fail_json(
                                msg="{0} profile backup failed on host {1}".format(prof_name, self.module_facts['hostname']),
                                changed=False,
                                stdout=out,
                                stderr=err
                    )
        elif "IHS" in p_name:
            _bkp_dirs = " ".join([f for f in os.listdir(path) if "conf" in f])
            _bkp_command = "tar -zcvf {2}/IHS_Config_Backup_{0}_{1}.tar.gz {3}".format(self.module_facts['hostname'], b_time, b_path, _bkp_dirs)
            _backup = self.exec_command(_bkp_command)
            out, err = _backup.communicate()
            if _backup.returncode != 0:
                self.module.fail_json(
                            msg="IHS backup failed on host {0}".format(self.module_facts['hostname']),
                            changed=False,
                            stdout=out,
                            stderr=err
                )
        elif "PLUGIN" in p_name:
            _bkp_command = "tar -zcvf {0}/PLUGIN_Backup_{1}_{2}.tar.gz {3}".format(b_path, self.module_facts['hostname'], b_time, path)
            _backup = self.exec_command(_bkp_command)
            out, err = _backup.communicate()
            if _backup.returncode != 0:
                self.module.fail_json(
                            msg="Plugin backup failed on host {0}".format(self.module_facts['hostname']),
                            changed=False,
                            stdout=out,
                            stderr=err
                )
        self.module_facts['backup_status'] = "DONE"
        
    
    def exec_command(self, cmdWithArgs):
            exe = subprocess.Popen(
                            [cmdWithArgs],
                            shell=True,
                            stdout = subprocess.PIPE,
                            stderr = subprocess.PIPE
            )
            return exe

    def _stop_running_processes(self, option, proc_pid):
        for proc in proc_pid:
            pid = proc_pid[proc]
            if "force" in option:
                self.force_kill_pid(pid)               
            else:
                self.kill_pid(pid)

            
    def kill_pid(self, pid):
        if self._check_pid_exists(pid):
            try:
                os.kill(int(pid), signal.SIGTERM)
                return True
            except OSError:
                return False
        return False
        
                
    def force_kill_pid(self, pid):
        if self._check_pid_exists(pid):
            try:
                os.kill(int(pid), signal.SIGKILL)
                return True
            except OSError:
                return False
        return False
            
        
    def _check_installed_version(self, packageId):    
        packs = subprocess.Popen(
            ["{0}/eclipse/tools/imcl "
		 " listInstalledPackages "
		 " -long".format(self.module.params['iimpath'])],
		shell=True,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
        )
        stdout_val, stderr_val = packs.communicate()

        #self.module_facts['check_stdout'] = stdout_val
        #self.module_facts['check_stderr'] = stderr_val      
        if packs.returncode != 0:
              self.module.fail_json(
                  msg="Failed to get the version of package '{0}'".format(packageId),
                  stdout=stdout_val,
                  stderr=stderr_val
              )              
        
        #_versions = []
        _fix_pattern = self._fix_pattern()
        latest_versions = []
        for line in stdout_val.splitlines():
            f_path = self.strip(self.indexOf(line, ":", 0))
            if(f_path == self.module.params['path']):
                fix_id = self.strip(self.indexOf(line, ":", 1))
                self._map_fix_types(packageId)
                latest_versions.append(self._base_version(_fix_pattern[self.module_facts['product']]['FixPack'], fix_id))
                #self.module_facts['installed_fixes'].update({self.module_facts['fixtype']:_versions.append(self._base_version(_fix_pattern[self.module_facts['product'], fix_id]))})
                #self.module_facts['installed_fixes'].append(self._extract_version(fix_id))
                if packageId in line:
                    #linesplit = self.indexOf(line, ":")
                    self.module_facts['installed'] = True
                    self.module_facts['path'] = self.strip(self.indexOf(line, ":", 0))
                    self.module_facts['fixid'] = self.strip(self.indexOf(line, ":", 1))
                    self.module_facts['name'] = self.strip(self.indexOf(line, ":", 2))
                    self.module_facts['version'] = self.strip(self.indexOf(line, ":", 3))
                    break
                else:
                    self.module_facts['installed'] = False
                    self.module_facts['fixid'] = packageId
            else:
                self.module_facts['installed'] = False
                self.module_facts['fixid'] = packageId
        #self.module_facts['installed_fixes'].update({self.module_facts['fixtype']:_versions})
        
        #_version = self.module_facts['installed_fixes']['FixPack']
        #self.module_facts['base_version'] = "{0}.{1}".format(_version[0][:_version[0].rfind(".")], "0")
        #self.module_facts['fix_version'] = {'FixPack':_version[0][_version[0].rfind(".")+1:]}
        self.module_facts['installed_version'] = " ".join([ver for ver in latest_versions if ver])
        return self.module_facts
    
    #get value from module facts.
    def getFact(self, key):
        return self.module_facts[key]
        
        
    def ibmPatchImpl(self, state, fixid, kill, path, bkpath, iimpath, repo):        
        self._get_os_facts()
        fix_id = self.indexOf(fixid, ',', 0)        
        if not self._check_provisioned("com.ibm.cic.agent", iimpath):
            self.module.fail_json(
                        changed=False,
                        moodule_facts=self.module_facts,
                        msg="IIM is not installed at {0} on host {1}".format(iimpath, self.module_facts['hostname'])
            )        
        self._check_installed_version(self.strip(fix_id))
        
        if(state == 'present'):
            if self.module.check_mode and not self.module_facts['installed']:
                self.module.exit_json(
                            changed=False,
                            module_facts=self.module_facts,
                            msg="IBM patch id {0} can be installed at path {1} on host - {2}".format(self.strip(fix_id), path, self.module_facts['hostname'])
                )
            elif self.module.check_mode and self.module_facts['installed']:
                self.module.exit_json(
                            changed=False,
                            module_facts = self.module_facts,
                            msg = "IBM Patch id {0} already installed at path {1} on host - {2}".format(self.strip(fix_id), path, self.module_facts['hostname'])
                )
                
            if not self._check_path_exists(repo):
                self.module.fail_json(
                            changed=False,
                            module_facts = self.module_facts,
                            msg="Requested patch id was not found in the repository"
                )
            if self.module_facts['installed']:            
                self.module.exit_json(
                            changed=False,
                            module_facts = self.module_facts,
                            msg = "IBM Patch id {0} already installed at path {1} on host - {2}".format(self.strip(fix_id), path, str(self.module_facts['hostname']))
                )
            self.module_facts['running_processes'] = self._map_proc_to_pid(self._get_running_processes(path))
            _proc_pids = self.module_facts['running_processes']
            _count = 0
            _option = "soft"
            if kill:
                while True:               
                    if not _proc_pids:
                        break
                    if (_count > 2):
                        _option = "force"
                    if(_count >= 5):
                        self.module.fail_json(
                                    changed=False,
                                    module_facts = self.module_facts,
                                    msg="Max threshold readed to stop the process - 5 retries with 15 seconds delay. Try to stop manually!."
                        )
                        break
                    self._stop_running_processes(_option, _proc_pids)
                    _count += 1
                    time.sleep(15)
                    
            self.backup_configuration(self.module_facts['product'], path, bkpath)
            patch = subprocess.Popen(
                                    ["{0}/eclipse/tools/imcl install {1} "
                                     " -repositories {2} "
                                     " -installationDirectory {3} "                                     
                                     " -acceptLicense ".format(iimpath, self.strip(fix_id), repo, path)
                                    ],
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
            )
            stdout_val, stderr_val = patch.communicate()

            if patch.returncode != 0:
                self.module.fail_json(
                            msg="IBM patch '{0}' installation failed".format(self.strip(fix_id)),
                            changed=False,
                            stdout=stdout_val,
                            stderr=stderr_val,
                            module_facts=self.module_facts
                )
                
            self._check_installed_version(self.strip(fix_id))
            if self.module_facts['installed']:
                self.module.exit_json(
                            msg="IBM patch {0} installed successfully at path {1} on host {2}!.".format(self.strip(fix_id), path, self.module_facts['hostname']),
                            changed=True,
                            #stdout=stdout_val,
                            #stderr=stderr_val,
                            module_facts=self.module_facts
                )
            else:
                self.module.fail_json(
                            msg="IBM patch {0} installation failed at path {1} on host {2}".format(self.strip(fix_id), path, self.module_facts['hostname']),
                            changed=False,
                            stdout=stdout_val,
                            stderr=stderr_val,
                            module_facts=self.module_facts
            
                )
        elif(state == 'absent'):
            if self.module.check_mode and self.module_facts['installed']:
                self.module.exit_json(
                            changed=False,
                            module_facts=self.module_facts,
                            msg="IBM patch id {0} can be rollback at path {1} on host - {2}".format(self.strip(fix_id), path, self.module_facts['hostname'])
                )
            elif self.module.check_mode and not self.module_facts['installed']:
                self.module.exit_json(
                            changed=False,
                            module_facts = self.module_facts,
                            msg = "IBM Patch id {0} not installed at path {1} on host - {2}".format(self.strip(fix_id), path, self.module_facts['hostname'])
                )
            if not self.module_facts['installed']:            
                self.module.exit_json(
                            changed=False,
                            module_facts = self.module_facts,
                            msg = "IBM Patch id {0} is not installed at path {1} on host - {2}".format(self.strip(fix_id), path, str(self.module_facts['hostname']))
                )
            self.module_facts['running_processes'] = self._map_proc_to_pid(self._get_running_processes(path))
            _proc_pids = self.module_facts['running_processes']
            if kill:
                _count = 0
                _option = "soft"
                while True:               
                    if not _proc_pids:
                            break
                    if (_count > 2):
                        _option = "force"
                    if(_count >= 5):
                        self.module.fail_json(
                                    changed=False,
                                    module_facts = self.module_facts,
                                    msg="Max threshold reached to stop the process - 5 retries with 15 seconds delay. Try to stop manually!."
                        )
                        break
                    self._stop_running_processes(_option, _proc_pids)
                    _count += 1
                    time.sleep(15)
            _rollback_patch = subprocess.Popen(
                                    ["{0}/eclipse/tools/imcl uninstall {1} "                                                                         
                                     " -acceptLicense ".format(iimpath, self.strip(fix_id))
                                    ],
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
            )
            stdout_val, stderr_val = _rollback_patch.communicate()
            if _rollback_patch.returncode != 0:
                self.module.fail_json(
                           msg="IBM patch '{0}' rollback failed".format(self.strip(fix_id)),
                            changed=False,
                            stdout=stdout_val,
                            stderr=stderr_val,
                            module_facts=self.module_facts
                )
                
            self._check_installed_version(self.strip(fix_id))
            if not self.module_facts['installed']:
                self.module.exit_json(
                            msg="IBM patch {0} rollback is successfull at path {1} on host {2}!.".format(self.strip(fix_id), path, self.module_facts['hostname']),
                            changed=True,
                            #stdout=stdout_val,
                            #stderr=stderr_val,
                            module_facts=self.module_facts
                )
            else:
                self.module.fail_json(
                            msg="IBM patch {0} rollback failed at path {1} on host {2}".format(self.strip(fix_id), path, self.module_facts['hostname']),
                            changed=False,
                            #stdout=stdout_val,
                            #stderr=stderr_val,
                            module_facts=self.module_facts
            
                )

    def main(self):
        empty = []
        state = self.module.params['state']
        if self._check_empty_vars(state):
            empty.append("state")
        fixid = self.module.params['fixid']
        if self._check_empty_vars(fixid):
            empty.append("fixid")
        kill = self.module.params['kill']        
        path = self.module.params['path']
        if self._check_empty_vars(path):
            empty.append("path")
        bkpath = self.module.params['bkpath']
        if self._check_empty_vars(bkpath):
            empty.append("bkpath")
        iimpath = self.module.params['iimpath']
        if self._check_empty_vars(iimpath):
            empty.append("iimpath")        
        repo = self.module.params['repo']
        if self._check_empty_vars(repo):
            empty.append("repo")
        
        if empty:
            self.module.fail_json(
                        msg="Don't specify null/empty auguments in the palybook.",
                        changed=False
            )
        else:
            self.ibmPatchImpl(state, fixid, kill, path, bkpath, iimpath, repo)        
        
#Executing main methind
        
if __name__ == '__main__':
    patch = ibm_patch()
    patch.main()
