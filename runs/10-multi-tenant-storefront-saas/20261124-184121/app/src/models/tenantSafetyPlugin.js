// A small plugin that ensures tenantId is present for writes and queries
module.exports = function tenantSafetyPlugin(schema) {
  // For save operations ensure tenantId exists
  schema.pre('save', function (next) {
    if (!this.tenantId) return next(new Error('tenantId is required'));
    next();
  });

  // For query middleware, check that a tenantId is part of the filter
  function ensureTenant(next) {
    const q = this.getQuery();
    if (!q || !Object.prototype.hasOwnProperty.call(q, 'tenantId')) {
      return next(new Error('Repository-safety: tenantId must be present in query filter'));
    }
    next();
  }

  schema.pre('find', ensureTenant);
  schema.pre('findOne', ensureTenant);
  schema.pre('updateOne', ensureTenant);
  schema.pre('findOneAndUpdate', ensureTenant);
  schema.pre('deleteOne', ensureTenant);
};
