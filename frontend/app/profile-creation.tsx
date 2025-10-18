import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  TouchableWithoutFeedback,
  Keyboard,
  Image,
  Alert
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { doc, setDoc, getDoc } from 'firebase/firestore';
import { db } from '../firebaseConfig';
import { getAuth } from 'firebase/auth';
const logo = require('../assets/images/dermascan_logo_transparent.png');

const auth = getAuth();

// Common diseases list
const COMMON_DISEASES = [
  'Diabetes', 'Hypertension', 'Heart Disease', 'Asthma', 'Arthritis',
  'Depression', 'Anxiety', 'High Cholesterol', 'Migraine', 'Obesity',
  'Cancer', 'Stroke', 'COPD', 'Kidney Disease', 'Liver Disease',
  'Thyroid Disease', 'Epilepsy', 'Osteoporosis', 'Sleep Apnea', 'IBD'
];

// Common allergies list
const COMMON_ALLERGIES = [
  'Penicillin', 'Sulfa', 'Aspirin', 'Ibuprofen', 'Latex',
  'Peanuts', 'Tree Nuts', 'Shellfish', 'Dairy', 'Eggs',
  'Soy', 'Wheat', 'Pollen', 'Dust Mites', 'Pet Dander',
  'Mold', 'Insect Stings', 'Contrast Dye', 'Nickel', 'Fragrances'
];

// Common family history conditions
const FAMILY_HISTORY_CONDITIONS = [
  'Heart Disease', 'Diabetes', 'Cancer', 'High Blood Pressure',
  'Stroke', 'Alzheimer\'s Disease', 'Depression', 'Anxiety',
  'Obesity', 'Asthma', 'Arthritis', 'Kidney Disease',
  'Liver Disease', 'Thyroid Disease', 'Epilepsy', 'Osteoporosis'
];

export default function ProfileCreationScreen() {
  const [currentStep, setCurrentStep] = useState(1);
  const [pastDiseases, setPastDiseases] = useState<string[]>([]);
  const [otherDiseases, setOtherDiseases] = useState<string[]>([]);
  const [newDisease, setNewDisease] = useState('');
  const [medications, setMedications] = useState<string[]>([]);
  const [newMedication, setNewMedication] = useState('');
  const [allergies, setAllergies] = useState<string[]>([]);
  const [otherAllergies, setOtherAllergies] = useState<string[]>([]);
  const [newAllergy, setNewAllergy] = useState('');
  const [familyHistory, setFamilyHistory] = useState<string[]>([]);
  const [newFamilyHistory, setNewFamilyHistory] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const totalSteps = 4;

  const handleDiseaseToggle = (disease: string) => {
    setPastDiseases(prev => 
      prev.includes(disease) 
        ? prev.filter(d => d !== disease)
        : [...prev, disease]
    );
  };

  const handleAddOtherDisease = () => {
    if (newDisease.trim() && !otherDiseases.includes(newDisease.trim())) {
      setOtherDiseases(prev => [...prev, newDisease.trim()]);
      setNewDisease('');
    }
  };

  const handleRemoveOtherDisease = (disease: string) => {
    setOtherDiseases(prev => prev.filter(d => d !== disease));
  };

  const handleAddMedication = () => {
    if (newMedication.trim() && !medications.includes(newMedication.trim())) {
      setMedications(prev => [...prev, newMedication.trim()]);
      setNewMedication('');
    }
  };

  const handleRemoveMedication = (medication: string) => {
    setMedications(prev => prev.filter(m => m !== medication));
  };

  const handleAllergyToggle = (allergy: string) => {
    setAllergies(prev => 
      prev.includes(allergy) 
        ? prev.filter(a => a !== allergy)
        : [...prev, allergy]
    );
  };

  const handleAddOtherAllergy = () => {
    if (newAllergy.trim() && !otherAllergies.includes(newAllergy.trim())) {
      setOtherAllergies(prev => [...prev, newAllergy.trim()]);
      setNewAllergy('');
    }
  };

  const handleRemoveOtherAllergy = (allergy: string) => {
    setOtherAllergies(prev => prev.filter(a => a !== allergy));
  };

  const handleAddFamilyHistory = () => {
    if (newFamilyHistory.trim() && !familyHistory.includes(newFamilyHistory.trim())) {
      setFamilyHistory(prev => [...prev, newFamilyHistory.trim()]);
      setNewFamilyHistory('');
    }
  };

  const handleRemoveFamilyHistory = (condition: string) => {
    setFamilyHistory(prev => prev.filter(f => f !== condition));
  };

  const handleSkip = async () => {
    setIsLoading(true);
    try {
      const user = auth.currentUser;
      if (user) {
        await setDoc(doc(db, 'users', user.uid), {
          profileCreated: false,
          profileSkipped: true,
          profileSkippedAt: new Date()
        }, { merge: true });
      }
      router.replace('/dashboard');
    } catch (error) {
      Alert.alert('Error', 'Failed to save profile status');
    } finally {
      setIsLoading(false);
    }
  };

  const handleComplete = async () => {
    setIsLoading(true);
    try {
      const user = auth.currentUser;
      if (user) {
        await setDoc(doc(db, 'users', user.uid), {
          profileCreated: true,
          profileCompletedAt: new Date(),
          medicalHistory: {
            pastDiseases: [...pastDiseases, ...otherDiseases],
            medications: medications,
            allergies: [...allergies, ...otherAllergies],
            familyHistory: familyHistory
          }
        }, { merge: true });
      }
      router.replace('/dashboard');
    } catch (error) {
      Alert.alert('Error', 'Failed to save profile');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStepIndicator = () => (
    <View style={styles.stepIndicator}>
      {Array.from({ length: totalSteps }, (_, index) => (
        <View
          key={index}
          style={[
            styles.stepDot,
            index + 1 <= currentStep ? styles.stepDotActive : styles.stepDotInactive
          ]}
        />
      ))}
    </View>
  );

  const renderStep1 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Past Diseases & Conditions</Text>
      <Text style={styles.stepSubtitle}>Select any conditions you have or have had in the past</Text>
      
      <ScrollView style={styles.checkboxContainer} showsVerticalScrollIndicator={false}>
        {COMMON_DISEASES.map((disease) => (
          <TouchableOpacity
            key={disease}
            style={styles.checkboxItem}
            onPress={() => handleDiseaseToggle(disease)}
          >
            <View style={[
              styles.checkbox,
              pastDiseases.includes(disease) && styles.checkboxSelected
            ]}>
              {pastDiseases.includes(disease) && (
                <Ionicons name="checkmark" size={16} color="#fff" />
              )}
            </View>
            <Text style={styles.checkboxText}>{disease}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <View style={styles.addItemContainer}>
        <TextInput
          style={styles.addItemInput}
          placeholder="Add other condition..."
          value={newDisease}
          onChangeText={setNewDisease}
          placeholderTextColor="#666"
        />
        <TouchableOpacity style={styles.addButton} onPress={handleAddOtherDisease}>
          <Ionicons name="add" size={20} color="#2c3e50" />
        </TouchableOpacity>
      </View>

      {otherDiseases.length > 0 && (
        <View style={styles.addedItemsContainer}>
          {otherDiseases.map((disease, index) => (
            <View key={index} style={styles.addedItem}>
              <Text style={styles.addedItemText}>{disease}</Text>
              <TouchableOpacity onPress={() => handleRemoveOtherDisease(disease)}>
                <Ionicons name="close-circle" size={20} color="#e74c3c" />
              </TouchableOpacity>
            </View>
          ))}
        </View>
      )}
    </View>
  );

  const renderStep2 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Current Medications</Text>
      <Text style={styles.stepSubtitle}>List any medications you are currently taking</Text>
      
      <View style={styles.addItemContainer}>
        <TextInput
          style={styles.addItemInput}
          placeholder="Enter medication name..."
          value={newMedication}
          onChangeText={setNewMedication}
          placeholderTextColor="#666"
        />
        <TouchableOpacity style={styles.addButton} onPress={handleAddMedication}>
          <Ionicons name="add" size={20} color="#2c3e50" />
        </TouchableOpacity>
      </View>

      {medications.length > 0 && (
        <View style={styles.addedItemsContainer}>
          {medications.map((medication, index) => (
            <View key={index} style={styles.addedItem}>
              <Text style={styles.addedItemText}>{medication}</Text>
              <TouchableOpacity onPress={() => handleRemoveMedication(medication)}>
                <Ionicons name="close-circle" size={20} color="#e74c3c" />
              </TouchableOpacity>
            </View>
          ))}
        </View>
      )}
    </View>
  );

  const renderStep3 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Allergies</Text>
      <Text style={styles.stepSubtitle}>Select any allergies you have</Text>
      
      <ScrollView style={styles.checkboxContainer} showsVerticalScrollIndicator={false}>
        {COMMON_ALLERGIES.map((allergy) => (
          <TouchableOpacity
            key={allergy}
            style={styles.checkboxItem}
            onPress={() => handleAllergyToggle(allergy)}
          >
            <View style={[
              styles.checkbox,
              allergies.includes(allergy) && styles.checkboxSelected
            ]}>
              {allergies.includes(allergy) && (
                <Ionicons name="checkmark" size={16} color="#fff" />
              )}
            </View>
            <Text style={styles.checkboxText}>{allergy}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <View style={styles.addItemContainer}>
        <TextInput
          style={styles.addItemInput}
          placeholder="Add other allergy..."
          value={newAllergy}
          onChangeText={setNewAllergy}
          placeholderTextColor="#666"
        />
        <TouchableOpacity style={styles.addButton} onPress={handleAddOtherAllergy}>
          <Ionicons name="add" size={20} color="#2c3e50" />
        </TouchableOpacity>
      </View>

      {otherAllergies.length > 0 && (
        <View style={styles.addedItemsContainer}>
          {otherAllergies.map((allergy, index) => (
            <View key={index} style={styles.addedItem}>
              <Text style={styles.addedItemText}>{allergy}</Text>
              <TouchableOpacity onPress={() => handleRemoveOtherAllergy(allergy)}>
                <Ionicons name="close-circle" size={20} color="#e74c3c" />
              </TouchableOpacity>
            </View>
          ))}
        </View>
      )}
    </View>
  );

  const renderStep4 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Family Medical History</Text>
      <Text style={styles.stepSubtitle}>Select any conditions that run in your family</Text>
      
      <View style={styles.addItemContainer}>
        <TextInput
          style={styles.addItemInput}
          placeholder="Enter family history condition..."
          value={newFamilyHistory}
          onChangeText={setNewFamilyHistory}
          placeholderTextColor="#666"
        />
        <TouchableOpacity style={styles.addButton} onPress={handleAddFamilyHistory}>
          <Ionicons name="add" size={20} color="#2c3e50" />
        </TouchableOpacity>
      </View>

      {familyHistory.length > 0 && (
        <View style={styles.addedItemsContainer}>
          {familyHistory.map((condition, index) => (
            <View key={index} style={styles.addedItem}>
              <Text style={styles.addedItemText}>{condition}</Text>
              <TouchableOpacity onPress={() => handleRemoveFamilyHistory(condition)}>
                <Ionicons name="close-circle" size={20} color="#e74c3c" />
              </TouchableOpacity>
            </View>
          ))}
        </View>
      )}
    </View>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1: return renderStep1();
      case 2: return renderStep2();
      case 3: return renderStep3();
      case 4: return renderStep4();
      default: return renderStep1();
    }
  };

  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.scrollContainer} showsVerticalScrollIndicator={false}>
          <View style={styles.header}>
            <Image source={logo} style={styles.logo} resizeMode="contain" />
            <Text style={styles.title}>Complete Your Profile</Text>
            <Text style={styles.subtitle}>Help us provide better medical assistance</Text>
            {renderStepIndicator()}
          </View>

          {renderCurrentStep()}

          <View style={styles.buttonContainer}>
            <View style={styles.navigationButtons}>
              {currentStep > 1 && (
                <TouchableOpacity style={styles.previousButton} onPress={handlePrevious}>
                  <Ionicons name="chevron-back" size={20} color="#2c3e50" />
                  <Text style={styles.previousButtonText}>Previous</Text>
                </TouchableOpacity>
              )}
              
              <View style={styles.rightButtons}>
                <TouchableOpacity style={styles.skipButton} onPress={handleSkip} disabled={isLoading}>
                  <Text style={styles.skipButtonText}>Skip</Text>
                </TouchableOpacity>
                
                {currentStep < totalSteps ? (
                  <TouchableOpacity style={styles.nextButton} onPress={handleNext}>
                    <Text style={styles.nextButtonText}>Next</Text>
                    <Ionicons name="chevron-forward" size={20} color="#fff" />
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity style={styles.completeButton} onPress={handleComplete} disabled={isLoading}>
                    <Text style={styles.completeButtonText}>Complete</Text>
                  </TouchableOpacity>
                )}
              </View>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  scrollContainer: {
    flexGrow: 1,
    paddingHorizontal: 20,
  },
  header: {
    alignItems: 'center',
    paddingVertical: 30,
  },
  logo: {
    width: 100,
    height: 100,
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#7f8c8d',
    textAlign: 'center',
    marginBottom: 30,
  },
  stepIndicator: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  stepDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginHorizontal: 4,
  },
  stepDotActive: {
    backgroundColor: '#2c3e50',
  },
  stepDotInactive: {
    backgroundColor: '#bdc3c7',
  },
  stepContainer: {
    flex: 1,
    paddingBottom: 20,
  },
  stepTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  stepSubtitle: {
    fontSize: 16,
    color: '#7f8c8d',
    marginBottom: 20,
  },
  checkboxContainer: {
    maxHeight: 300,
    marginBottom: 20,
  },
  checkboxItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    marginBottom: 8,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#bdc3c7',
    marginRight: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxSelected: {
    backgroundColor: '#2c3e50',
    borderColor: '#2c3e50',
  },
  checkboxText: {
    fontSize: 16,
    color: '#2c3e50',
    flex: 1,
  },
  addItemContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  addItemInput: {
    flex: 1,
    height: 42,
    borderColor: '#ddd',
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 14,
    backgroundColor: '#f9f9f9',
    color: '#000',
    marginRight: 10,
  },
  addButton: {
    width: 42,
    height: 42,
    backgroundColor: '#ecf0f1',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addedItemsContainer: {
    marginTop: 10,
  },
  addedItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#e8f5e8',
    borderRadius: 8,
    marginBottom: 8,
  },
  addedItemText: {
    fontSize: 14,
    color: '#27ae60',
    flex: 1,
  },
  buttonContainer: {
    paddingVertical: 20,
  },
  navigationButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  rightButtons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  previousButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  previousButtonText: {
    fontSize: 16,
    color: '#2c3e50',
    marginLeft: 4,
  },
  skipButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    marginRight: 10,
  },
  skipButtonText: {
    fontSize: 16,
    color: '#7f8c8d',
  },
  nextButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2c3e50',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
  },
  nextButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: 'bold',
    marginRight: 4,
  },
  completeButton: {
    backgroundColor: '#27ae60',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
  },
  completeButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: 'bold',
  },
});
