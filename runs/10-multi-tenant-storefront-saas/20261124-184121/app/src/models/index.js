const { mongoose } = require('../mongoose');
const ProductSchema = require('./product');
const InventorySchema = require('./inventory');
const OrderSchema = require('./order');

const Product = mongoose.model('Product', ProductSchema);
const Inventory = mongoose.model('Inventory', InventorySchema);
const Order = mongoose.model('Order', OrderSchema);

module.exports = { Product, Inventory, Order };
