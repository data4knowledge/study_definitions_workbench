<h5>Access</h5>
<p>Go to <a href="https://d4k-sdw.fly.dev/" target="_blank">https://d4k-sdw.fly.dev/</a></p>
<img src="/static/images/docs/user_guide/image1.png" class="img-fluid rounded mt-2 mb-3" alt="Splash Page">
<p>Click on the large button.</p>
<p><em>Note:</em></p>
<ol>
  <li><em>The version will change as time passes</em></li>
  <li><em>The tooling is a beta, expect one or two issues.</em></li>
</ol>

<h5>Sign Up &amp; Login</h5>
<p>You should see a login / sign up screen.</p>
<img src="/static/images/docs/user_guide/image2.png" class="img-fluid rounded mt-2 mb-3" style="max-width: 400px;" alt="Login Screen">
<p>If you do not have an account, please sign up using the available options (email / password, Google, GitHub, Apple or Microsoft - not Office365). Otherwise, login as normal.</p>

<h5>Home Page</h5>
<p>You should see the home page. On first entering the system no data will be loaded. You can always return to the home page by clicking the "Home" menu option (top right) or clicking the logo image (top left).</p>
<img src="/static/images/docs/user_guide/image3.png" class="img-fluid rounded mt-2 mb-3" alt="Home Page">

<h5>Import Data</h5>
<p>Currently three types of import are supported:</p>
<ol>
  <li>M11 Word Document (.docx)</li>
  <li>M11 FHIR Message (.json)</li>
  <li>USDM Excel (.xlsx)</li>
</ol>
<p>Example M11 Word or USDM Excel files are available via the Help -> Examples (top right) menu.</p>
<p>When data is imported the system maintains separate versions for each study and by type of import. For example, Protocol X loaded from a M11 '.docx' file is kept separate from Protocol X loaded from a FHIR JSON file. This allows them to be compared. The coloured pills indicate the type of load (see below).</p>

<h5>M11 Protocol in MS Word (.docx) Import</h5>
<p>Click on the import menu and select the M11 Document option. The import page will be displayed.</p>
<img src="/static/images/docs/user_guide/image6.png" class="img-fluid rounded mt-2 mb-3" alt="Import M11 Protocol">
<p>Click "Choose Files" and use the normal file selection mechanism to select a single M11 Protocol Word document.</p>
<p>Click "Upload File(s)". The system will respond saying the file is uploaded and then shortly after a "success" message should appear as follows.</p>
<img src="/static/images/docs/user_guide/image7.png" class="img-fluid rounded mt-2 mb-3" alt="Import M11 Success">
<p>Return to the home page. An entry for the file loaded should be present containing high level information about the protocol. Note the blue "M11 Document" load type indicator.</p>
<img src="/static/images/docs/user_guide/image8.png" class="img-fluid rounded mt-2 mb-3" alt="Home with M11 Study">

<h5>M11 Protocol in FHIR V1 Message (.json) Import</h5>
<p>Click on the import menu and select the M11 FHIR v1 option. The import page will be displayed.</p>
<img src="/static/images/docs/user_guide/image9.png" class="img-fluid rounded mt-2 mb-3" alt="Import FHIR JSON">
<p>Click "Choose Files" and use the normal file selection mechanism to select a single M11 FHIR JSON file.</p>
<p>Click "Upload File(s)". The system will respond saying the file is uploaded and then shortly after a "success" message should appear as follows.</p>
<img src="/static/images/docs/user_guide/image10.png" class="img-fluid rounded mt-2 mb-3" alt="Import FHIR Success">
<p>Return to the home page. An entry for the protocol loaded should be present. Note the red "FHIR" type indicator.</p>
<img src="/static/images/docs/user_guide/image11.png" class="img-fluid rounded mt-2 mb-3" alt="Home with M11 and FHIR Studies">

<h5>USDM in MS Excel (.xlsx) Import</h5>
<p>Click on the import menu and select the USDM Excel option. The import page will be displayed.</p>
<img src="/static/images/docs/user_guide/image12.png" class="img-fluid rounded mt-2 mb-3" alt="Import USDM Excel">
<p>Click "Choose Files" and use the normal file selection mechanism to select a single USDM Excel file and any associated image files required to render the protocol document.</p>
<img src="/static/images/docs/user_guide/image13.png" class="img-fluid rounded mt-2 mb-3" alt="Import USDM Excel with Files">
<p>Click "Upload File(s)". The system will respond saying the file is uploaded and then shortly after a "success" message should appear. Return to the home page.</p>
<img src="/static/images/docs/user_guide/image14.png" class="img-fluid rounded mt-2 mb-3" alt="Home with USDM Excel Study">

<h5>Side By Side Page</h5>
<p>Select two or more protocols by clicking on the relevant items (anywhere in the boxes), you should see a blue border around the selected items. Click again to de-select, it is just a toggle.</p>
<img src="/static/images/docs/user_guide/image15.png" class="img-fluid rounded mt-2 mb-3" alt="Multiple Studies">
<img src="/static/images/docs/user_guide/image16.png" class="img-fluid rounded mt-2 mb-3" alt="Studies with Selection">
<p>Click the "List Selected Studies" button. You should see something like the following.</p>
<img src="/static/images/docs/user_guide/image17.png" class="img-fluid rounded mt-2 mb-3" alt="Title Page Comparison">
<p>Click on the Home button (top right) or the logo (top left) to get back to the home page.</p>

<h5>Details Page</h5>
<p>From the home page, clicking the "View Details" button for a study will get you to the details view. Use the view menu at the top to see the other views.</p>
<img src="/static/images/docs/user_guide/image18.png" class="img-fluid rounded mt-2 mb-3" alt="Details Page">

<h5>Export</h5>
<p>The Export menu on the details view page allows for a study to be exported as a</p>
<ol>
  <li>FHIR v1 message in JSON format</li>
  <li>USDM model in JSON format</li>
  <li>The protocol rendering as a PDF</li>
</ol>
<p>The downloads work in the standard way.</p>

<h5>Version History and Differences</h5>
<p>The version history for a given study / protocol and import type can be viewed via the details page. The USDM JSON can be viewed and, if multiple versions are stored, the differences can be inspected.</p>
<img src="/static/images/docs/user_guide/image19.png" class="img-fluid rounded mt-2 mb-3" alt="Version History">
<img src="/static/images/docs/user_guide/image20.png" class="img-fluid rounded mt-2 mb-3" alt="USDM JSON View">
<img src="/static/images/docs/user_guide/image21.png" class="img-fluid rounded mt-2 mb-3" alt="USDM JSON Diff">
