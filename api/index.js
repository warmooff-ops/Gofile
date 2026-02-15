const { createClient } = require('@vercel/node');

// Simple Node.js handler as fallback
module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  
  try {
    const response = {
      success: true,
      message: 'GoFile Scanner API is working!',
      status: 'ready',
      method: req.method,
      timestamp: new Date().toISOString()
    };
    
    res.status(200).json(response);
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
      message: 'Internal server error'
    });
  }
};
