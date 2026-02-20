<h5>General</h5>
<p>This document is a short guide on launching the M11 Study Definitions Workbench (SDW) application from within the precisionFDA environment.</p>

<h5>Login</h5>
<p>Login to the precisionFDA environment in the normal manner using your normal username, password and 2FA mechanism.</p>

<h5>Launch the M11 SDW Application</h5>
<p>Once logged in access the SDW application via the PRISM portal.</p>
<img src="/static/images/docs/prism/image-000.png" class="img-fluid rounded mt-2 mb-3" alt="PRISM Portal">
<p>You should see the following page.</p>
<img src="/static/images/docs/prism/image-001.png" class="img-fluid rounded mt-2 mb-3" alt="App Configuration">
<p>Click on "Run App" button (bottom left) to start the application launch process.</p>

<h5>M11 SDW Application Execution</h5>
<p>A virtual server will be launched running the M11 SDW application. The following page should be seen.</p>
<img src="/static/images/docs/prism/image-002.png" class="img-fluid rounded mt-2 mb-3" alt="Application Starting">
<p>Once the server is running additional buttons and a pop-up will be displayed. Launching the server may take several minutes (typically 3 or 4 minutes).</p>
<img src="/static/images/docs/prism/image-003.png" class="img-fluid rounded mt-2 mb-3" alt="Application Running">
<p>Click the "Open Workstation" button (top right) to enter the server environment.</p>
<p>A new tab will be opened in the browser displaying a terminal interface. A prompt will be displayed.</p>
<ol>
  <li>Respond "y" to the first prompt.</li>
  <li>A second prompt will be displayed.</li>
  <li>Choose either "private" or "space" as desired.</li>
  <li>A list of directories will be displayed.</li>
  <li>Enter the id of the folder to be copied at the third prompt.</li>
  <li>Finally, a URL will be displayed</li>
</ol>
<p>The SDW application is single user version of a web server application and therefore needs to run on a virtual server within the precisionFDA environment. This virtual server does not have access to your workspace or any shared spaces so, for the application to have access to the desired files, there is a need to copy the contents you select to the virtual server.</p>
<p><em>NOTE: We may make this part of the application in the future to make the launch process smoother.</em></p>
<p>The terminal page should look something like the following once you have responded to all the prompts. Note the final URL.</p>
<img src="/static/images/docs/prism/image-004.png" class="img-fluid rounded mt-2 mb-3" alt="Terminal with URL">
<p>Copy the URL and paste into the address bar of a new tab within your browser. The application splash page will be displayed.</p>
<img src="/static/images/docs/prism/image-005.png" class="img-fluid rounded mt-2 mb-3" alt="SDW Splash Page">
<p>The version number may change in the future as updates are made to the application.</p>
<p>Click on the large button. A user page will be displayed. Note the legend in the middle top stating "PRISM" and "SINGLE" denoting the application detecting it is running within the precisionFDA environment in single user mode.</p>
<img src="/static/images/docs/prism/image-006.png" class="img-fluid rounded mt-2 mb-3" alt="User Details Page">
<p>Click on either the "Home" button (top right) or the logo (top left) to go to the home screen.</p>
<img src="/static/images/docs/prism/image-007.png" class="img-fluid rounded mt-2 mb-3" alt="PRISM Home Page">
<p>Because the application is launched every time the application will not contain any data.</p>
<p>Please refer to the general user guide for the SDW application for further directions on using the SDW application.</p>
