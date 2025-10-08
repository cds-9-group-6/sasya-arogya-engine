# 🧪 Sasya Arogya Engine Periodic Testing System

## Overview

This periodic testing system is designed to continuously validate the Sasya Arogya Engine's functionality in an OpenShift Kubernetes cluster. The system runs comprehensive test suites every 2 hours to ensure the engine is working correctly across all major features.

## 🎯 Test Categories

### 1. **CNN Classification Tests** (4 test cases)
- **Rice Leaf Blight Classification** - Tests disease detection in rice plants
- **Apple Leaf Disease Classification** - Tests disease detection in apple trees
- **Tomato Disease Classification** - Tests disease detection in tomato plants
- **Wheat Rust Classification** - Tests disease detection in wheat plants

### 2. **Prescription Recommendation Tests** (5 test cases)
- **Disease-specific Treatments** - Based on classification results
- **General Disease Treatment** - For common plant diseases
- **Organic Treatment Options** - For eco-friendly solutions
- **Sequential Testing** - Always follows classification tests

### 3. **Insurance Premium Calculation Tests** (4 test cases)
- **Wheat Premium Calculation** - 5 hectares in Punjab
- **Rice Premium Calculation** - 3 hectares in Tamil Nadu
- **Tomato Premium Calculation** - 2 hectares in Maharashtra
- **Cotton Premium Calculation** - 4 hectares in Gujarat

### 4. **Insurance Certificate Generation Tests** (3 test cases)
- **Wheat Insurance Purchase** - Complete purchase flow
- **Rice Insurance Purchase** - Certificate generation
- **Tomato Insurance Purchase** - PDF generation

### 5. **General Crop Care Tests** (8 test cases)
- **Soil Watering Tips** - Watering frequency advice
- **Weather Tips for Rice** - Weather condition guidance
- **Soil Preparation** - Pre-planting soil advice
- **Fertilizer Advice** - Nutrient management
- **Pest Control** - Natural pest management
- **Harvesting Tips** - Optimal harvest timing
- **Crop Rotation** - Rotation planning
- **Seasonal Care** - Season-specific advice

### 6. **Non-Crop Intent Tests** (5 test cases)
- **Weather Query** - Non-agricultural weather questions
- **General Chat** - Casual conversation
- **Off-topic Questions** - Non-agricultural topics
- **Technical Support** - App-related issues
- **Random Text** - Invalid input handling

## 🔧 Key Features

### **Session Management**
- **Unique Session IDs**: Format `fsm_session_dd_mm_yyyy_hh_mm`
- **Time-based Generation**: Each test run gets a unique session
- **Session Persistence**: Maintains context across test categories

### **Test Randomization**
- **Configurable Limits**: Max tests per category (default: 3)
- **Random Selection**: Prevents predictable test patterns
- **Sequential Dependencies**: Prescription tests always follow classification

### **Comprehensive Coverage**
- **15-20 Test Cases**: Covers all major engine functionalities
- **Image-based Testing**: Uses actual plant disease images
- **Real-world Scenarios**: Tests realistic user interactions
- **Error Handling**: Tests both success and failure scenarios

## 📁 File Structure

```
├── test_engine_periodic.py          # Main Python test script
├── run_periodic_tests.sh            # Shell script runner
├── k8s-periodic-tests.yaml          # Kubernetes CronJob configuration
├── PERIODIC_TESTING_README.md       # This documentation
└── resources/
    └── images_for_test/             # Test images directory
        ├── rice_leaf_blight.jpg
        ├── apple_leaf_disease.jpg
        ├── tomato_disease.jpg
        └── wheat_rust.jpg
```

## 🚀 Deployment in OpenShift

### 1. **Prerequisites**
- OpenShift cluster with appropriate permissions
- Sasya Arogya Engine deployed and running
- Storage class available for test results

### 2. **Deploy Test Scripts**
```bash
# Create namespace
oc create namespace sasya-arogya

# Apply Kubernetes configuration
oc apply -f k8s-periodic-tests.yaml

# Verify CronJob is created
oc get cronjobs -n sasya-arogya
```

### 3. **Manual Testing**
```bash
# Test with default engine URL
./run_periodic_tests.sh

# Test with custom engine URL
./run_periodic_tests.sh http://sasya-engine-service:8080

# Test with custom parameters
./run_periodic_tests.sh -t 5 -p python3.11 http://localhost:8080

# Show help
./run_periodic_tests.sh --help
```

### 4. **Configure Test Images**
```bash
# Add test images to ConfigMap
oc create configmap sasya-engine-test-images \
  --from-file=resources/images_for_test/ \
  -n sasya-arogya
```

### 5. **Monitor Test Execution**
```bash
# View CronJob status
oc get cronjobs -n sasya-arogya

# View recent jobs
oc get jobs -n sasya-arogya

# View job logs
oc logs job/sasya-engine-periodic-tests-<timestamp> -n sasya-arogya

# View test results
oc exec -it <pod-name> -n sasya-arogya -- ls -la /tmp/sasya_engine_tests/
```

## ⚙️ Configuration

### **Environment Variables**
- `SASYA_ENGINE_URL`: Engine service URL (default: http://localhost:8080)
- `MAX_TESTS_PER_CATEGORY`: Max tests per category (default: 3)
- `NOTIFICATION_WEBHOOK`: Webhook URL for notifications (optional)

### **Kubernetes Configuration**
- **Schedule**: Every 2 hours (`0 */2 * * *`)
- **Timeout**: 10 minutes per job
- **Resources**: 256Mi memory, 100m CPU (requests)
- **Storage**: 1Gi for test results

## 📊 Test Results

### **Output Format**
```json
{
  "session_id": "fsm_session_15_12_2024_14_30",
  "timestamp": "2024-12-15T14:30:00Z",
  "duration_seconds": 45.2,
  "total_tests": 18,
  "successful_tests": 17,
  "failed_tests": 1,
  "success_rate": 94.4,
  "results": {
    "CNN Classification": [...],
    "Prescription Recommendations": [...],
    "Insurance Premium Calculation": [...],
    "Insurance Certificate Generation": [...],
    "General Crop Care": [...],
    "Non-Crop Intent": [...]
  }
}
```

### **Log Files**
- **Location**: `/tmp/sasya_engine_tests/`
- **Format**: `periodic_test_YYYYMMDD_HHMMSS.log`
- **Retention**: Last 10 log files kept
- **Content**: Detailed test execution logs

## 🔍 Monitoring and Alerting

### **Health Checks**
- **Engine Availability**: HTTP health check before tests
- **Test Success Rate**: Track overall success percentage
- **Response Times**: Monitor engine performance
- **Error Patterns**: Identify recurring issues

### **Notifications** (Optional)
- **Webhook Integration**: Send results to external systems
- **Success Notifications**: Confirm test completion
- **Failure Alerts**: Notify on test failures
- **Performance Alerts**: Alert on slow responses

## 🛠️ Troubleshooting

### **Common Issues**

#### **Engine Not Responding**
```bash
# Check engine health
curl http://sasya-engine-service:8080/health

# Check service status
oc get svc -n sasya-arogya

# Check pod logs
oc logs -l app=sasya-engine -n sasya-arogya
```

#### **Test Images Missing**
```bash
# Verify test images ConfigMap
oc get configmap sasya-engine-test-images -n sasya-arogya -o yaml

# Check mounted images
oc exec -it <pod-name> -n sasya-arogya -- ls -la /app/resources/images_for_test/
```

#### **Test Failures**
```bash
# View detailed logs
oc logs job/sasya-engine-periodic-tests-<timestamp> -n sasya-arogya

# Check test results
oc exec -it <pod-name> -n sasya-arogya -- cat /tmp/sasya_engine_tests/test_results_<timestamp>.json
```

### **Debug Mode**
```bash
# Run tests manually for debugging
oc run debug-tester --image=python:3.11-slim -it --rm --restart=Never \
  --env="SASYA_ENGINE_URL=http://sasya-engine-service:8080" \
  --command -- /bin/bash
```

## 📈 Performance Metrics

### **Expected Performance**
- **Total Test Duration**: 2-5 minutes
- **Success Rate**: >90%
- **Response Time**: <2 seconds per test
- **Memory Usage**: <512Mi per job
- **CPU Usage**: <500m per job

### **Scaling Considerations**
- **Concurrent Jobs**: Limit to prevent resource contention
- **Test Frequency**: Adjust based on system capacity
- **Resource Limits**: Monitor and adjust as needed
- **Storage Growth**: Clean up old test results periodically

## 🔄 Maintenance

### **Regular Tasks**
- **Log Cleanup**: Remove old log files
- **Result Cleanup**: Archive old test results
- **Image Updates**: Update test images as needed
- **Configuration Updates**: Adjust test parameters

### **Monitoring**
- **Success Rate Trends**: Track performance over time
- **Error Analysis**: Identify common failure patterns
- **Resource Usage**: Monitor CPU and memory consumption
- **Storage Usage**: Track test result storage growth

## 🎯 Best Practices

### **Test Design**
- **Realistic Scenarios**: Use real-world test cases
- **Comprehensive Coverage**: Test all major features
- **Sequential Dependencies**: Maintain proper test order
- **Error Scenarios**: Include failure case testing

### **Deployment**
- **Resource Limits**: Set appropriate resource constraints
- **Health Checks**: Implement proper health monitoring
- **Logging**: Enable comprehensive logging
- **Alerting**: Set up failure notifications

### **Maintenance**
- **Regular Updates**: Keep test cases current
- **Performance Monitoring**: Track system performance
- **Cleanup**: Regular cleanup of old data
- **Documentation**: Keep documentation updated

---

**🌾 The periodic testing system ensures the Sasya Arogya Engine maintains high reliability and performance in production environments!**
