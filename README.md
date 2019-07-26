# Add users to groups using Python LDAP

**Purpose of this project:**

To add users to group in a given secure cluster. 

**How to run this script?**

```python
./sc_ldap.py <username> <groupname>
```

In the below example, user `suhass` is added to group `acad` in Secure Cluster.

```python
# ./sc_ldap.py suhass acad
('suhass', 'acad')
Homedirectory created
755 permissions applied
Ownership and default group assigned
Connection closed
```

**Project workflow:**

1. If a user exists in global LDAP and does not exist in secure cluster LDAP, then get the user-attributes from global LDAP and add him into SC. Also, create a new home-directory for the user within SC. Home directory creation process is handled by `new_homedir.py` script. It consists of three parts: 
   1. Create a home-directory if it does not exist
   2. Change the permissions to 755
   3. Change ownership based on uid and gid attributes from global LDAP user-attributes
2. If a user already exists in SC LDAP, then add a user to a given group.
3. If a user does not exist in global LDAP, then report `Invalid User`.
