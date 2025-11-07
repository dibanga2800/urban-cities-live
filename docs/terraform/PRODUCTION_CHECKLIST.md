# Production Deployment Checklist

Use this checklist before deploying to production.

## ✅ Pre-Deployment

### Security
- [ ] Changed SQL admin password from default
- [ ] Reviewed and updated firewall rules
- [ ] Configured network security groups (if needed)
- [ ] Set up Azure Key Vault for secrets management
- [ ] Enabled Azure AD authentication (if applicable)
- [ ] Reviewed role assignments and permissions

### Configuration
- [ ] Verified `terraform.tfvars` settings
- [ ] Updated resource names for production
- [ ] Confirmed Azure subscription and region
- [ ] Set appropriate SKUs for production workloads
- [ ] Configured tags for cost tracking

### Backup & Recovery
- [ ] Enabled SQL Database backup retention
- [ ] Configured storage account replication
- [ ] Documented disaster recovery procedures
- [ ] Tested restore procedures

### Monitoring
- [ ] Set up Azure Monitor alerts
- [ ] Configured diagnostic settings
- [ ] Enabled Application Insights (if needed)
- [ ] Set up log analytics workspace

## ✅ Deployment

- [ ] Run `terraform plan` and review changes
- [ ] Save plan output: `terraform plan -out=prod.tfplan`
- [ ] Review plan with team/stakeholders
- [ ] Apply with saved plan: `terraform apply prod.tfplan`
- [ ] Verify all resources created successfully
- [ ] Document all outputs and connection strings

## ✅ Post-Deployment

### Verification
- [ ] Test SQL Database connectivity
- [ ] Verify ADLS Gen2 container access
- [ ] Test Data Factory pipelines
- [ ] Verify role assignments working correctly
- [ ] Test application connections

### Security Hardening
- [ ] Enable resource locks on critical resources
- [ ] Configure audit logging
- [ ] Enable Microsoft Defender for Cloud
- [ ] Review and restrict public network access
- [ ] Enable encryption at rest (should be default)

### Documentation
- [ ] Document connection strings (securely)
- [ ] Update team documentation
- [ ] Share access credentials securely
- [ ] Document any custom configurations
- [ ] Update runbooks/operational procedures

### Compliance
- [ ] Verify compliance with organizational policies
- [ ] Document data residency requirements
- [ ] Review privacy and data protection settings
- [ ] Ensure logging meets audit requirements

## ✅ Ongoing Operations

### Regular Maintenance
- [ ] Schedule regular Terraform plan checks for drift
- [ ] Review Azure Advisor recommendations
- [ ] Monitor costs and optimize resources
- [ ] Review security recommendations monthly
- [ ] Update Terraform providers quarterly

### Incident Response
- [ ] Document incident response procedures
- [ ] Set up alerting to appropriate teams
- [ ] Test backup/restore procedures quarterly
- [ ] Document rollback procedures

## 🚨 Before Destroy

If you ever need to destroy resources:
- [ ] Export and backup all critical data
- [ ] Document all configurations
- [ ] Notify all stakeholders
- [ ] Disable any dependent applications
- [ ] Run `terraform plan -destroy` first
- [ ] Get approval before running `terraform destroy`

## 📞 Contacts

**Infrastructure Team:**
- Azure Subscription Owner: _________________
- Terraform Maintainer: _________________
- On-Call Engineer: _________________

**Emergency Contacts:**
- Azure Support: _________________
- Internal IT Help: _________________

---

**Last Reviewed:** November 4, 2025  
**Next Review:** _________________
