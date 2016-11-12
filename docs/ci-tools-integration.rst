.. _ci_tools_integration:

=========================
Integration with CI tools
=========================

``wft4galaxy`` can be easly integrated with `Continous Integration (CI) tools` like `Jenkins <https://jenkins.io/>`_.

As a workflow developer, you could create a repository (e.g., Git) for hosting your workflow as well as its tests, which can be defined as ``wft4galaxy`` tests.

Thus, you should enrich your repository with:

  1. `definition test file`, which will contain the definition all worflow tests (see :ref:`config_file` for more information);
  2. every resource refenced in the definition file above, such as input and expected output datasets.

Finally, you should configure your CI tool:

  (a) to be notified every time a changes happens in your wofkflow repository;
  (b) to start wft4galaxy tests.

How to pratically put in place points (a) and (b) strictly depends on the CI tool you choose. But, in principle, you should configure your tool to launch wft4galaxy for running tests in the definition files you have stored in your workflow repository.

.. note::  Rember that to actually launch **wft4galaxy** from your CI tool you have three alternatives:

  1. **wft4galaxy** script, if wft4galaxy is installed and accessible from execution environment of your CI tool or you install it as a step of your CI tool project;
  2. **wft4galaxy-docker** script,  which can be downloaded on the fly and used to run wft4galaxy tests within a Docker container (in such a case, your CI tool must support Docker);
  3. **direct docker usage** (see :ref:`notebooks/6_direct_docker_usage.ipynb` as example).


Jenkins Integration
===================

An example of procedure for configuring a Jenkins project to work with wft4galaxy:

  1. create a new `free style software project`;
  2. set your Git repository in the project box;
  3. set Git as your `Source Code Management` and then the URL of your Git repository;
  4. check the box `Build when a change is pushed to Github`;
  5. add a new `Execute Shell` build step;
  6. in the box of `Execute Shell` step call the ``wft4galaxy`` tool to run your workflow tests (see note above);
  7. save the configuration of your Jenkins project;
  8. set the proper `Webhook` in your GitHub repository to allow your Jenkins instance to be notified when a change happens (i.e., in `Webhooks & Services > Jenkins plugin` put the URL of your Jenkins instance).
