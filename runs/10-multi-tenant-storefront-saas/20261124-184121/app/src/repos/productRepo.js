class ProductRepo {
  constructor(models, tenantId) {
    if (!tenantId) throw new Error('tenantId is required to create a repository');
    this.tenantId = tenantId;
    this.Product = models.Product;
  }

  async createOrUpdate(product) {
    // ensure tenantId cannot be overridden
    product.tenantId = this.tenantId;
    const filter = { tenantId: this.tenantId, sku: product.sku };
    return this.Product.findOneAndUpdate(filter, product, { upsert: true, new: true, setDefaultsOnInsert: true });
  }

  async findBySku(sku) {
    return this.Product.findOne({ tenantId: this.tenantId, sku }).lean();
  }

  async listAll() {
    return this.Product.find({ tenantId: this.tenantId }).lean();
  }
}

module.exports = ProductRepo;
