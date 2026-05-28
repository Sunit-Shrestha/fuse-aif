SCHEMA = """
Tables:
- productlines (productLine, textDescription, htmlDescription, image)
- products (productCode, productName, productLine, productScale, productVendor, productDescription, quantityInStock, buyPrice, MSRP)
- offices (officeCode, city, phone, addressLine1, addressLine2, state, country, postalCode, territory)
- employees (employeeNumber, lastName, firstName, extension, email, officeCode, reportsTo, jobTitle)
- customers (customerNumber, customerName, contactLastName, contactFirstName, phone, addressLine1, addressLine2, city, state, postalCode, country, salesRepEmployeeNumber, creditLimit)
- orders (orderNumber, orderDate, requiredDate, shippedDate, status, comments, customerNumber)
- orderdetails (orderNumber, productCode, quantityOrdered, priceEach, orderLineNumber)
- payments (customerNumber, checkNumber, paymentDate, amount)
"""

