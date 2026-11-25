class OrderRepo {
  constructor(models, tenantId) {
    if (!tenantId) throw new Error('tenantId is required to create a repository');
    this.tenantId = tenantId;
    this.Order = models.Order;
  }

  async createOrder(order) {
    order.tenantId = this.tenantId;
    order.createdAt = order.createdAt || new Date();
    return this.Order.create(order);
  }

  async listRecent(limit = 10) {
    return this.Order.find({ tenantId: this.tenantId }).sort({ createdAt: -1 }).limit(limit).lean();
  }
}

module.exports = OrderRepo;
