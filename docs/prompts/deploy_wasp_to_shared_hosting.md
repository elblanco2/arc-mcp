# Deploy Wasp App to Shared Hosting Prompt

This prompt helps guide you through the process of deploying a Wasp web application from GitHub to a shared hosting account using the Arc MCP server.

## Instructions for Claude

Hi Arc, I need your help deploying a specific version of my Wasp web application from GitHub to my shared hosting account.

Here are the details:

1. **Framework:** Wasp
2. **Source Code:**
   * GitHub Repository URL: [REPOSITORY_URL]
   * Version to Deploy: [GIT_VERSION] <!-- Git Commit Hash, Tag, or Branch Name -->
3. **Hosting Provider:** Shared Hosting (using FTP/SFTP)
4. **Destination Path on Server:** [DESTINATION_PATH] <!-- E.g., /public_html/my-wasp-app -->

**Action Plan:**

* First, I need to make sure you have the correct credentials for my shared hosting account. Please guide me through using the `authenticate_provider` tool if we haven't done this before, or confirm if you already have credentials stored for this host. My hosting details are:
  * Host: [HOST]
  * Username: [USERNAME]
  * Password: [PASSWORD]
  * Port: [PORT] <!-- E.g., 21 for FTP, 22 for SFTP -->
  * Protocol: [PROTOCOL] <!-- ftp or sftp -->
* Next, I have cloned the repository locally to this path: `[LOCAL_PATH]` and checked out the specific version `[GIT_VERSION]`.
* Please use the `analyze_requirements` tool for the 'wasp' framework and 'shared_hosting' provider on that local path. Let me know what environment variables are needed and if there are any compatibility concerns or preparation steps.
* Based on the analysis, please confirm the configuration for deployment. I'd like to enable the backup option (`backup: true`) and use the default 'smart' sync mode (`sync_mode: 'smart'`). We might need to set environment variables during the build – let me know what the analysis suggests.
* Once we've confirmed the configuration, please proceed with the deployment using the `deploy_framework` tool.
* Finally, report back the results, including the number of files uploaded/skipped and the final deployment URL if available. If any errors occur, please provide the details so we can troubleshoot.

Let's start with the authentication step.

## Explanation

This prompt provides all the necessary information for the Arc MCP server to deploy a Wasp application to a shared hosting environment. The user needs to:

1. Replace the placeholders (text in [BRACKETS]) with their specific information
2. Send the prompt to Claude with the Arc MCP server enabled
3. Follow the guided conversation to complete the deployment

The prompt guides Claude through:
- Authenticating with the hosting provider
- Analyzing the Wasp project requirements
- Configuring the deployment options
- Executing the deployment
- Reporting the results

## Technical Details

The Arc MCP server will execute the following steps behind the scenes:

1. **Authentication**: Stores credentials securely for the shared hosting provider
2. **Analysis**: Examines the Wasp project structure to determine:
   - Required environment variables
   - Build commands and output directory
   - Compatibility with the shared hosting environment
3. **Deployment**:
   - Builds the Wasp project using `wasp build`
   - Creates a backup of the existing files on the server (if enabled)
   - Uploads the built files to the specified destination directory
   - Uses smart synchronization to only upload changed files

## Tips

- Make sure the local repository is up-to-date and the correct version is checked out
- Have your shared hosting credentials ready
- Make note of any required environment variables from the analysis step
- Consider creating a backup before deployment (enabled by default)
- The smart sync mode will only upload files that have changed, making deployments faster
