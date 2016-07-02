Homepage and documentation source for Ansible
=============================================

This project hosts the source behind [docs.ansible.com](http://docs.ansible.com/)

Contributions to the documentation are welcome.  To make changes, submit a pull request
that changes the reStructuredText files in the "rst/" directory only, and the core team can
do a docs build and push the static files. 

If you wish to verify output from the markup
such as link references, you may install sphinx and build the documentation by running
`make viewdocs` from the `ansible/docsite` directory.  

To include module documentation you'll need to run `make webdocs` at the top level of the repository.  The generated
html files are in docsite/htmlout/.

If you do not want to learn the reStructuredText format, you can also [file issues] about
documentation problems on the Ansible GitHub project.

Note that module documentation can actually be [generated from a DOCUMENTATION docstring][module-docs]
in the modules directory, so corrections to modules written as such need to be made
in the module source, rather than in docsite source.

To install sphinx and the required theme, install pip and then "pip install sphinx sphinx_rtd_theme"

[file issues]: https://github.com/ansible/ansible/issues
[module-docs]: http://docs.ansible.com/developing_modules.html#documenting-your-module


