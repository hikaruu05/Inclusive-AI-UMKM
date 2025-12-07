import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:open_file/open_file.dart';
import '../services/api_service.dart';

class BookOcrScreen extends StatefulWidget {
  const BookOcrScreen({super.key});

  @override
  State<BookOcrScreen> createState() => _BookOcrScreenState();
}

class _BookOcrScreenState extends State<BookOcrScreen> {
  File? _imageFile;
  final ImagePicker _picker = ImagePicker();
  final ApiService _apiService = ApiService();
  bool _isProcessing = false;
  Map<String, dynamic>? _ocrResult;
  
  Future<void> _pickImage(ImageSource source) async {
    final XFile? image = await _picker.pickImage(source: source);
    if (image != null) {
      setState(() {
        _imageFile = File(image.path);
        _ocrResult = null;
      });
    }
  }

  Future<void> _processBookReport() async {
    if (_imageFile == null) {
      _showSnackBar('Pilih gambar terlebih dahulu', Colors.red);
      return;
    }

    setState(() => _isProcessing = true);

    try {
      final result = await _apiService.convertBookToExcel(_imageFile!);
      
      setState(() {
        _ocrResult = result;
      });
      
      _showSnackBar('Berhasil mengekstrak data!', Colors.green);
    } catch (e) {
      _showSnackBar('Gagal: $e', Colors.red);
    } finally {
      setState(() => _isProcessing = false);
    }
  }
  
  Future<void> _downloadExcel() async {
    if (_ocrResult == null || _ocrResult!['file_id'] == null) {
      _showSnackBar('Tidak ada file untuk didownload', Colors.red);
      return;
    }
    
    try {
      setState(() => _isProcessing = true);
      
      final directory = await getApplicationDocumentsDirectory();
      final savePath = '${directory.path}/laporan_${DateTime.now().millisecondsSinceEpoch}.xlsx';
      
      await _apiService.downloadExcel(_ocrResult!['file_id'], savePath);
      
      _showSnackBar('File berhasil didownload!', Colors.green);
      
      // Open the file
      await OpenFile.open(savePath);
    } catch (e) {
      _showSnackBar('Gagal download: $e', Colors.red);
    } finally {
      setState(() => _isProcessing = false);
    }
  }

  void _showSnackBar(String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: color),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header Card
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
                    '📖 Konversi Buku ke Excel',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 20,
                      color: Colors.white,
                    ),
                  ),
                  SizedBox(height: 12),
                  Text(
                    'Ubah foto halaman buku laporan menjadi data Excel dengan teknologi AI OCR',
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 24),
            
            // Info Card
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFFF0F4FF),
                border: Border.all(color: const Color(0xFFE0EAFF)),
                borderRadius: BorderRadius.circular(12),
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '📋 Cara Penggunaan:',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                      color: Color(0xFF667EEA),
                    ),
                  ),
                  const SizedBox(height: 12),
                  _InfoStep(
                    number: 1,
                    text: 'Ambil foto halaman buku laporan',
                  ),
                  const SizedBox(height: 8),
                  _InfoStep(
                    number: 2,
                    text: 'Pastikan tulisan jelas dan pencahayaan baik',
                  ),
                  const SizedBox(height: 8),
                  _InfoStep(
                    number: 3,
                    text: 'Klik "Proses OCR" untuk ekstrak data',
                  ),
                  const SizedBox(height: 8),
                  _InfoStep(
                    number: 4,
                    text: 'Download hasil dalam format Excel',
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 24),
            
            // Image Preview
            if (_imageFile != null)
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
                    height: 350,
                    fit: BoxFit.cover,
                  ),
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
                    Icon(
                      Icons.image_outlined,
                      size: 64,
                      color: Color(0xFFB0B0B0),
                    ),
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
                    label: const Text('Ambil Foto'),
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
                    label: const Text('Dari Galeri'),
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
            
            // Process Button
            ElevatedButton.icon(
              onPressed: _isProcessing ? null : _processBookReport,
              icon: _isProcessing 
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : const Icon(Icons.auto_awesome),
              label: Text(
                _isProcessing ? 'Memproses...' : 'Proses OCR',
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
            
            // Results Section
            if (_ocrResult != null) ...[
              const SizedBox(height: 24),
              Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      const Color(0xFF10B981).withOpacity(0.1),
                      const Color(0xFF10B981).withOpacity(0.05),
                    ],
                  ),
                  border: Border.all(color: const Color(0xFF10B981).withOpacity(0.3)),
                  borderRadius: BorderRadius.circular(12),
                ),
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: const Color(0xFF10B981),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(
                            Icons.check_circle,
                            color: Colors.white,
                            size: 24,
                          ),
                        ),
                        const SizedBox(width: 12),
                        const Text(
                          'Hasil Ekstraksi',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 18,
                            color: Color(0xFF059669),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Container(
                      height: 1,
                      color: const Color(0xFF10B981).withOpacity(0.2),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: _ResultItem(
                            icon: Icons.table_rows,
                            label: 'Baris',
                            value: '${_ocrResult!['rows_extracted'] ?? 0}',
                          ),
                        ),
                        Container(
                          width: 1,
                          height: 40,
                          color: const Color(0xFF10B981).withOpacity(0.2),
                        ),
                        Expanded(
                          child: _ResultItem(
                            icon: Icons.view_column,
                            label: 'Kolom',
                            value: '${_ocrResult!['columns_detected'] ?? 0}',
                          ),
                        ),
                      ],
                    ),
                    if (_ocrResult!['preview'] != null) ...[
                      const SizedBox(height: 8),
                      const Text(
                        'Preview Data:',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          _ocrResult!['preview'],
                          style: const TextStyle(
                            fontFamily: 'monospace',
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              
              const SizedBox(height: 16),
              
              // Download Button
              ElevatedButton.icon(
                onPressed: _isProcessing ? null : _downloadExcel,
                icon: const Icon(Icons.download),
                label: const Text('Download Excel'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  backgroundColor: const Color(0xFF10B981),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  elevation: 0,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _InfoStep extends StatelessWidget {
  final int number;
  final String text;

  const _InfoStep({
    required this.number,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 28,
          height: 28,
          decoration: BoxDecoration(
            color: const Color(0xFF667EEA),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Center(
            child: Text(
              '$number',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 14,
              color: Color(0xFF333333),
              height: 1.4,
            ),
          ),
        ),
      ],
    );
  }
}

class _ResultItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _ResultItem({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: const Color(0xFF10B981), size: 28),
        const SizedBox(height: 6),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: Color(0xFF666666),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Color(0xFF059669),
          ),
        ),
      ],
    );
  }
}
