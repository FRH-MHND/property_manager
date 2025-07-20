# Property Manager

A comprehensive property management system for ERPNext that handles rental units, tenant management, contracts, and automated rent collection with invoicing.

## Features

### Core Functionality
- **Property Management**: Manage multiple properties with detailed information
- **Rental Unit Management**: Track individual units with furnished/unfurnished status
- **Tenant Management**: Complete tenant profiles with contact and financial information
- **Rental Contracts**: Flexible contracts with various payment frequencies
- **Automated Rent Scheduling**: Generate payment schedules based on contract terms
- **Sales Invoice Integration**: Automatic invoice creation when rent is paid

### Payment Frequencies Supported
- Monthly
- Weekly
- Bi-weekly
- Quarterly
- Annually

### Key Features
- **Furnished/Unfurnished Units**: Track unit furnishing status
- **Flexible Payment Terms**: Support for various payment frequencies
- **Automated Late Fees**: Configurable grace periods and late fee calculations
- **Contract Management**: Full lifecycle management from draft to termination
- **Payment Tracking**: Complete payment history and outstanding balance tracking
- **ERPNext Integration**: Seamless integration with ERPNext's accounting system

## Installation

1. Copy the app to your Frappe bench apps directory
2. Install the app to your site:
   ```bash
   bench --site your-site install-app property_manager
   ```
3. Run migrations:
   ```bash
   bench --site your-site migrate
   ```

## Usage

### Setting Up Properties
1. Create a new Property with basic information
2. Add Rental Units to the property
3. Set base rent amounts and furnishing status for each unit

### Managing Tenants
1. Create Tenant records with complete contact information
2. Include emergency contacts and financial details
3. Track credit scores and employment information

### Creating Rental Contracts
1. Create a new Rental Contract
2. Select tenant and rental unit
3. Set contract dates and payment terms
4. Submit the contract to activate it and generate rent schedules

### Processing Rent Payments
1. View Rent Schedule entries for due payments
2. Mark payments as received
3. Sales invoices are automatically created upon payment
4. Track overdue payments and late fees

## DocTypes

### Property
- Property name and address information
- Property type (Residential, Commercial, etc.)
- Owner contact details
- Total units count

### Rental Unit
- Unit number and type
- Furnished/unfurnished status
- Base rent amount and security deposit
- Current occupancy status
- Unit amenities and features

### Tenant
- Personal and contact information
- Emergency contact details
- Financial information (income, credit score)
- Employment details

### Rental Contract
- Tenant and unit assignment
- Contract dates and terms
- Payment frequency and amounts
- Late fee and grace period settings
- Contract status tracking

### Rent Schedule
- Automated payment schedule generation
- Payment tracking and status
- Late fee calculations
- Sales invoice integration

## Automation Features

### Scheduled Tasks
- **Daily**: Mark overdue rent payments
- **Monthly**: Generate upcoming rent schedules for long-term contracts

### Document Events
- **Contract Submission**: Automatically generates rent schedules
- **Payment Recording**: Creates sales invoices when rent is paid
- **Unit Status Updates**: Automatically updates unit occupancy status

## Customization

The app is designed to be easily customizable:
- Add custom fields to any doctype
- Modify payment frequency options
- Customize late fee calculations
- Add additional automation rules

## Support

For support and customization requests, please contact the development team.

## License

MIT License

