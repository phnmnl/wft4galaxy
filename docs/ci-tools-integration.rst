.. _ci_tools_integration:

=========================
Integration with CI tools
=========================

``wft4galaxy`` can be easily integrated with `Continous Integration` (CI) tools like `Jenkins <https://jenkins.io/>`_.

A typical approach is to create a repository (e.g., Git) to host your workflow and its tests, which can be defined as ``wft4galaxy`` tests.  
More specifically, ,the repository needs to include:

  1. the `test definition file`, containing the definition all workflow tests (see :ref:`config_file` for more information);
  2. every resource referenced in the definition file above, such as input and expected output datasets.

Finally, for proper continuous integration you should configure your CI tool:

  (a) to be notified every time a changes are committed to your workflow repository;
  (b) to start wft4galaxy tests automatically.

How do this in practice depends on the specific CI tool you choose. However, in principle you'll need to configure your tool to launch ``wft4galaxy`` to run the tests defined for your workflows.

.. note::  Remember that to run wft4galaxy from your CI tool you have three alternatives:

  1. **wft4galaxy** script, if wft4galaxy is installed and accessible from your CI tool's execution environment or if you install wft4galaxy as a step in your CI testing script;
  2. **wft4galaxy-docker** script,  which can be downloaded on the fly and used to run wft4galaxy tests within a Docker container (in this case, your CI tool must support Docker);
  3. **direct docker usage** (see :ref:`notebooks/6_direct_docker_usage.ipynb` for an example).


Jenkins Integration
===================

To configure a Jenkins project to use `wft4galaxy` to test workflows hosted on
Github, follow this procedure.

  1. Create a new `free style software project`;
  2. Set your Git repository in the project box;
  3. Set Git as your `Source Code Management` and then the URL of your Git repository;
  4. Check the box `Build when a change is pushed to Github`;
  5. Add a new `Execute Shell` build step;
  6. From the `Execute Shell` box  call the ``wft4galaxy`` tool to run your workflow tests (see note above);
  7. Save the configuration of your Jenkins project;
  8. Set the proper `Webhook` in your GitHub repository to notify the Jenkins instance when a change happens (i.e., in `Webhooks & Services > Jenkins plugin` put the URL of your Jenkins instance).
