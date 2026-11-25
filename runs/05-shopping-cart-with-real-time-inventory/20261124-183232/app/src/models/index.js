const mongoose = require('mongoose');
const InventorySchema = require('./inventory');
const CartSchema = require('./cart');

const Inventory = mongoose.model('Inventory', InventorySchema);
const Cart = mongoose.model('Cart', CartSchema);

module.exports = { Inventory, Cart };
