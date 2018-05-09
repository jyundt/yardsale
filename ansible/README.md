# ansible
## Deploying
TL;DR 
```
ansible-playbook site.yml
```
## Version
Tested with ansible 2.5.2, but I suspect almost any version should work.

## Config
### Inventory
Update `hosts` to reflect the current hostname/IP of the `yardsale` server
### Vault
All secrets are kept in `group_vars/all/vault.yml` and are encrypted using ansible-vault

Additional sensitive files (like the GAPPS json key) may also be encrypted to allow for this to be hosted publicly.
