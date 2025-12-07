import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../providers/payment_provider.dart';

class PaymentUploadScreen extends StatefulWidget {
  const PaymentUploadScreen({super.key});

  @override
  State<PaymentUploadScreen> createState() => _PaymentUploadScreenState();
}

class _PaymentUploadScreenState extends State<PaymentUploadScreen> {
  File? _imageFile;
  final ImagePicker _picker = ImagePicker();
  bool _isProcessing = false;
  Map<String, dynamic>? _result;
  String? _validationStatus; // VALID, INVALID, or ERROR
  final TextEditingController _descriptionController = TextEditingController();

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? image = await _picker.pickImage(source: source);
      if (image != null) {
        setState(() {
          _imageFile = File(image.path);
          _result = null;
          _validationStatus = null;
        });
        
        // Auto-validate QRIS after image selection
        _validateQRIS();
      }
    } catch (e) {
      _showSnackBar('Error picking image: $e', Colors.orange);
    }
  }

  Future<void> _validateQRIS() async {
    if (_imageFile == null) return;
    
    setState(() => _isProcessing = true);
    
    try {
      final paymentProvider = Provider.of<PaymentProvider>(context, listen: false);
      final result = await paymentProvider.uploadPaymentScreenshot(_imageFile!);
      
      if (mounted) {
        setState(() {
          _result = result;
          _validationStatus = result['is_valid'] == true ? 'VALID' : 'INVALID';
        });
        
        // Show validation result
        final isValid = result['is_valid'] == true;
        _showSnackBar(
          isValid ? '✅ Pembayaran Valid!' : '❌ Pembayaran Invalid',
          isValid ? Colors.green : Colors.red,
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _validationStatus = 'ERROR');
        _showSnackBar('Validation error: $e', Colors.red);
      }
    } finally {
      if (mounted) {
        setState(() => _isProcessing = false);
      }
    }
  }

  Future<void> _uploadPayment() async {
    if (_imageFile == null) {
      _showSnackBar('Pilih gambar terlebih dahulu', Colors.red);
      return;
    }

    // Already validated automatically, just show result
    if (_result != null) {
      _showSnackBar('Screenshot sudah divalidasi!', Colors.green);
    }
  }

  void _showSnackBar(String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: color),
    );
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Instructions Card
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  const Color(0xFF667EEA).withOpacity(0.9),
                  const Color(0xFF764BA2).withOpacity(0.9),
                ],
              ),
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF667EEA).withOpacity(0.2),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text(
                  '📸 Upload Screenshot Pembayaran',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                    color: Colors.white,
                  ),
                ),
                SizedBox(height: 12),
                Text(
                  '✓ Ambil screenshot dari notifikasi bank/e-wallet',
                  style: TextStyle(color: Colors.white70, fontSize: 13),
                ),
                SizedBox(height: 6),
                Text(
                  '✓ Pastikan nominal dan waktu terlihat jelas',
                  style: TextStyle(color: Colors.white70, fontSize: 13),
                ),
                SizedBox(height: 6),
                Text(
                  '✓ AI akan otomatis validasi pembayaran Anda',
                  style: TextStyle(color: Colors.white70, fontSize: 13),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 24),
          
          // Image Preview
          if (_imageFile != null && !kIsWeb)
            Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Image.file(
                  _imageFile!,
                  height: 400,
                  fit: BoxFit.cover,
                ),
              ),
            )
          else if (_imageFile != null && kIsWeb)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFECFDF5),
                border: Border.all(color: const Color(0xFF10B981)),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(Icons.check_circle, color: Color(0xFF10B981), size: 28),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      '✅ Image selected: ${_imageFile!.path.split('/').last}',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF10B981),
                      ),
                    ),
                  ),
                ],
              ),
            )
          else
            Container(
              height: 300,
              decoration: BoxDecoration(
                border: Border.all(color: const Color(0xFFE0E0E0), width: 2),
                borderRadius: BorderRadius.circular(16),
                color: const Color(0xFFF7F7F7),
              ),
              child: const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.image_outlined, size: 64, color: Color(0xFFB0B0B0)),
                  SizedBox(height: 12),
                  Text(
                    'Belum ada gambar dipilih',
                    style: TextStyle(
                      color: Color(0xFF999999),
                      fontSize: 16,
                    ),
                  ),
                ],
              ),
            ),
          
          const SizedBox(height: 20),
          
          // Image Source Buttons
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _pickImage(ImageSource.camera),
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Kamera'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF667EEA),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    elevation: 0,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _pickImage(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library),
                  label: const Text('Galeri'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF764BA2),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    elevation: 0,
                  ),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 20),
          
          // Validation Status Indicator
          if (_validationStatus != null) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: _validationStatus == 'VALID'
                    ? const Color(0xFFECFDF5)
                    : _validationStatus == 'INVALID'
                        ? const Color(0xFFFFEBEE)
                        : const Color(0xFFFEF3C7),
                border: Border.all(
                  color: _validationStatus == 'VALID'
                      ? const Color(0xFFD1FAE5)
                      : _validationStatus == 'INVALID'
                          ? const Color(0xFFFECACA)
                          : const Color(0xFFFDE68A),
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: _validationStatus == 'VALID'
                          ? const Color(0xFF10B981)
                          : _validationStatus == 'INVALID'
                              ? const Color(0xFFFF6B6B)
                              : const Color(0xFFF59E0B),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(
                      _validationStatus == 'VALID'
                          ? Icons.check_circle
                          : _validationStatus == 'INVALID'
                              ? Icons.cancel
                              : Icons.info,
                      color: Colors.white,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _validationStatus == 'VALID'
                              ? 'Pembayaran Valid'
                              : _validationStatus == 'INVALID'
                                  ? 'Pembayaran Invalid'
                                  : 'Pemeriksaan Gagal',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: _validationStatus == 'VALID'
                                ? const Color(0xFF059669)
                                : _validationStatus == 'INVALID'
                                    ? const Color(0xFFDC2626)
                                    : const Color(0xFFB45309),
                            fontSize: 14,
                          ),
                        ),
                        if (_result != null && _result!['details'] != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            '${_result!['details']}',
                            style: TextStyle(
                              fontSize: 12,
                              color: _validationStatus == 'VALID'
                                  ? const Color(0xFF059669)
                                  : _validationStatus == 'INVALID'
                                      ? const Color(0xFFDC2626)
                                      : const Color(0xFFB45309),
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
          ],
          
          // Description Input Field
          const Text(
            'Deskripsi Pembelian',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _descriptionController,
            maxLines: 3,
            decoration: InputDecoration(
              hintText: 'Masukkan deskripsi pembelian (mis: Bahan baku, nama produk, jumlah item, dll)',
              hintStyle: const TextStyle(
                color: Color(0xFFB0B0B0),
                fontSize: 14,
              ),
              filled: true,
              fillColor: const Color(0xFFF7F7F7),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(
                  color: const Color(0xFFE0E0E0),
                  width: 1.5,
                ),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(
                  color: Color(0xFF667EEA),
                  width: 2,
                ),
              ),
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 14,
              ),
            ),
            style: const TextStyle(fontSize: 14),
          ),
          
          const SizedBox(height: 24),
          
          // Upload Button
          ElevatedButton.icon(
            onPressed: _isProcessing
                ? null
                : (_imageFile == null
                    ? null
                    : _uploadPayment),
            icon: _isProcessing
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.5,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  )
                : const Icon(Icons.check_circle),
            label: Text(
              _isProcessing ? 'Memvalidasi...' : 'Simpan Pembayaran',
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF667EEA),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              elevation: 0,
              disabledBackgroundColor: const Color(0xFF667EEA).withOpacity(0.5),
            ),
          ),
        ],
      ),
    );
  }
}
