class InventoryRepo {
  constructor(models, tenantId) {
    if (!tenantId) throw new Error('tenantId is required to create a repository');
    this.tenantId = tenantId;
    this.Inventory = models.Inventory;
  }

  async upsertInventory(sku, quantity) {
    const filter = { tenantId: this.tenantId, sku };
    const update = { $set: { quantity, updatedAt: new Date() }, $setOnInsert: { tenantId: this.tenantId, sku } };
    return this.Inventory.updateOne(filter, update, { upsert: true });
  }

  async getInventory(sku) {
    return this.Inventory.findOne({ tenantId: this.tenantId, sku }).lean();
  }
}

module.exports = InventoryRepo;
