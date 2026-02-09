#[cfg(test)]
mod tests {
    use super::*;
    use tokio;

    #[tokio::test]
    async fn test_unified_identity_creation() {
        let manager = UnifiedTrustManager::new();
        let temp_dir = tempfile::tempdir().unwrap();
        
        let identity = manager.create_identity(temp_dir.path()).unwrap();
        
        assert!(!identity.node_id.is_empty());
        assert_eq!(identity.trust_level, TrustLevel::New);
    }

    #[tokio::test]
    async fn test_peer_registration() {
        let manager = UnifiedTrustManager::new();
        
        let result = manager.register_peer(
            "test_peer".to_string(), 
            vec![0u8; 32]
        ).await;
        
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_trust_evaluation() {
        let manager = UnifiedTrustManager::new();
        
        // Register a peer first
        manager.register_peer("test_peer".to_string(), vec![0u8; 32]).await.unwrap();
        
        // Test trust evaluation
        let evaluation = manager.evaluate_trust("test_peer", "SYN").await;
        
        assert!(evaluation.allowed);
        assert_eq!(evaluation.trust_level, TrustLevel::New);
    }

    #[tokio::test]
    async fn test_resource_allocation() {
        let manager = UnifiedResourceManager::new();
        
        let request = ResourceRequest {
            component: "test_component".to_string(),
            resource_type: ResourceType::CpuCores,
            amount: 1.0,
            priority: Priority::Medium,
            duration: Some(60),
        };
        
        let result = manager.allocate_resource(request).await;
        
        assert!(result.is_ok());
        let allocation = result.unwrap();
        assert_eq!(allocation.component, "test_component");
        assert_eq!(allocation.resource_type, ResourceType::CpuCores);
    }

    #[tokio::test]
    async fn test_policy_enforcement() {
        let manager = UnifiedResourceManager::new();
        
        // Try to allocate more than allowed
        let request = ResourceRequest {
            component: "test_component".to_string(),
            resource_type: ResourceType::CpuCores,
            amount: 10.0, // Exceeds policy limit of 4.0
            priority: Priority::Medium,
            duration: Some(60),
        };
        
        let result = manager.allocate_resource(request).await;
        
        assert!(matches!(result, Err(AllocationError::ExceedsPolicyLimit)));
    }

    #[tokio::test]
    async fn test_replay_detection() {
        let manager = UnifiedTrustManager::new();
        let nonce = "test_nonce_123";
        
        // First use should be OK
        let is_replay1 = manager.is_replay(nonce).await;
        assert!(!is_replay1);
        
        // Second use should be detected as replay
        let is_replay2 = manager.is_replay(nonce).await;
        assert!(is_replay2);
    }

    #[tokio::test]
    async fn test_trust_promotion() {
        let manager = UnifiedTrustManager::new();
        
        // Register peer
        manager.register_peer("promotable_peer".to_string(), vec![0u8; 32]).await.unwrap();
        
        // Check initial trust level
        let initial_level = manager.get_trust_level("promotable_peer").await;
        assert_eq!(initial_level, TrustLevel::New);
        
        // Promote trust
        manager.promote_trust("promotable_peer").await.unwrap();
        
        // Check promoted level
        let promoted_level = manager.get_trust_level("promotable_peer").await;
        assert_eq!(promoted_level, TrustLevel::Probation);
    }

    #[tokio::test]
    async fn test_system_metrics() {
        let manager = UnifiedResourceManager::new();
        
        let metrics = manager.get_system_metrics().await;
        
        assert!(metrics.cpu_utilization >= 0.0);
        assert!(metrics.memory_utilization >= 0.0);
        assert!(metrics.network_utilization >= 0.0);
        assert_eq!(metrics.active_allocations, 0);
    }
}