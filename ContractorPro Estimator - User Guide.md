ContractorPro Estimator - User Guide

Welcome to ContractorPro Estimator! This guide will help you navigate and use the application to manage your construction projects and create estimates.

---

1.  **Main Application Window (Dashboard)**

    * **Project List:** This table displays all your saved projects.
    * **Search Bar:** Use the search bar at the top to quickly find projects by Project Name or Client Name. Just type in your search term, and the list will filter automatically.
    * **"Add New Project" Button:** Click this button to open a new "Project General Info" window, allowing you to create a new project from scratch.
    * **"Open General Info" Button:** Select a project from the list and click this button to open the "Project General Info" window for that specific project. This allows you to view and edit its core details.
    * **"Open Line Items" Button:** Select a project from the list and click this button to open the "Estimate Line Items" window for that project. This is where you will build your project estimates by adding materials, labor, and services.
    * **"Delete Selected Project" Button:** Select a project from the list and click this button to permanently remove it from the database. Use with caution!

---

2.  **Project General Info Window**

    This window allows you to manage the essential details of each project.

    * **General Info Section:**
        * **Project ID:** (Automatically assigned for new projects) A unique identifier for the project.
        * **Project Name:** The primary name for your project (e.g., "Smith Kitchen Remodel"). (Required)
        * **Client Name:** The name of your client. (Required)
        * **Client Contact:** The primary contact person for the client.
        * **Client Phone:** The client's primary phone number.
        * **Client Email:** The client's primary email address.

    * **Project Address Section:**
        * **Street:** The street address of the project site.
        * **City:** The city of the project site.
        * **State:** The state of the project site.
        * **ZIP:** The ZIP code of the project site.

    * **Schedule & Status Section:**
        * **Estimate Date:** The date the estimate was prepared.
        * **Bid Due Date:** The deadline for submitting the bid.
        * **Project Status:** The current status of the project (e.g., New, Bidding, Active, Completed).
        * **Contract Type:** The type of contract for the project (e.g., Fixed Price, Time & Materials).

    * **Scope & Notes Section:**
        * **Scope of Work:** A detailed description of the work to be performed for the project.
        * **Project Notes:** Any additional internal notes or comments related to the project.

    * **"Save Project Details" Button:** Click this button to save all changes made in this window to the database. The window will close automatically upon successful save.

---

3.  **Estimate Line Items Window**

    This window is where you build the detailed cost estimate for a selected project.

    * **Project Name / Project ID:** Displays the name and ID of the project you are currently estimating.
    * **Line Item Details Section:**
        * **Common Item:** A dropdown list of pre-defined common items (materials, labor, services). Selecting one will auto-populate Description, Category, and UOM.
        * **Cost Code:** A dropdown list of MasterFormat cost codes. Selecting one will auto-populate Description.
        * **Description:** A detailed description of the line item (e.g., "2x4x8 Stud").
        * **Category:** The type of item (e.g., Material, Labor, Service).
        * **Unit of Measure (UOM):** The unit in which the item is measured (e.g., EA for Each, LF for Linear Foot, HR for Hour).
        * **Quantity:** The number of units required for this line item.
        * **Unit Cost:** The cost per unit of the item.
        * **Total Item Cost:** (Automatically calculated) Quantity * Unit Cost.

    * **"Manage Common Items / Cost Codes" Button:** Click this to open a separate window where you can add, update, or delete your frequently used items and MasterFormat cost codes.

    * **Line Item Action Buttons:**
        * **"Add Line Item" Button:** Adds the details from the "Line Item Details" section as a new line item to the project's estimate.
        * **"Update Line Item" Button:** Select an existing line item in the table, modify its details in the input fields, and click this button to save the changes.
        * **"Delete Line Item" Button:** Select one or more line items from the table and click this button to remove them from the estimate.
        * **"Clear Form" Button:** Clears all input fields in the "Line Item Details" section.

    * **Line Item Table:** Displays all the line items added to the current project's estimate.
        * **ID:** Unique identifier for the line item.
        * **Description, Category, UOM, Quantity, Unit Cost, Total:** Columns reflecting the details of each line item.

    * **Financial Summary Section:**
        * **Markup Percentage:** The percentage added to the direct cost.
        * **Overhead Percentage:** The percentage for overhead costs.
        * **Profit Percentage:** The desired profit margin percentage.
        * **Total Direct Cost:** The sum of all "Total Item Cost" values.
        * **Total Overhead:** Calculated based on the Total Direct Cost and Overhead Percentage.
        * **Total Profit:** Calculated based on the Total Direct Cost (or Direct Cost + Overhead, depending on your formula) and Profit Percentage.
        * **Final Project Estimate:** The grand total estimate for the project, including direct costs, overhead, and profit.

    * **"Generate PDF Estimate" Button:** (Functionality to be implemented) This button will generate a professional PDF document of your project estimate.

---

4.  **Manage Common Items & Cost Codes Window**

    This window allows you to pre-define and manage your frequently used materials, labor, services, and industry-standard cost codes.

    * **"Common Items (Materials, Labor, Services)" Tab:**
        * **Name:** The name of the item (e.g., "2x4x8 Stud", "Electrician").
        * **Description:** A more detailed description of the item.
        * **Unit:** The default unit of measure for this item (e.g., "EA", "HR").
        * **Type:** Specifies if the item is "Material", "Labor", or "Service".
        * **MF Code (Optional):** You can link a MasterFormat code to a common item.
        * **"Add Item" Button:** Adds the entered item to your common items list.
        * **"Update Selected Item" Button:** Select an item from the table, modify the details above, and click to update.
        * **"Delete Selected Item" Button:** Select one or more items and click to delete them.
        * **Table:** Displays your list of common items.

    * **"Cost Codes" Tab:**
        * **Code:** The MasterFormat code (e.g., "03 30 00").
        * **Name:** The name associated with the code (e.g., "Cast-in-Place Concrete").
        * **Description (Optional):** A detailed description for the cost code.
        * **MF Division:** The MasterFormat division name (e.g., "03 - Concrete").
        * **"Add Code" Button:** Adds the new cost code.
        * **"Update Selected Code" Button:** Select a code, modify its details, and click to update.
        * **"Delete Selected Code" Button:** Select one or more codes and click to delete them.
        * **Table:** Displays your list of MasterFormat cost codes.

---

**Getting Started:**

1.  **Add a New Project:** Click "Add New Project" on the main dashboard and fill in the general information. Save the project.
2.  **Add Line Items:** Select your newly created project on the dashboard and click "Open Line Items." Use the Common Items, Cost Codes, or manual input to add materials, labor, and services.
3.  **Manage Common Data:** Before or during estimating, populate your "Manage Common Items & Cost Codes" lists to streamline your estimating process.

---

Thank you for using ContractorPro Estimator!