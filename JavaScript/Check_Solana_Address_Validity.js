const { PublicKey } = require('@solana/web3.js');
try {
    const publicKey = new PublicKey("Your PublicKey Here");
    console.log("地址有效:", publicKey.toString());
} catch (err) {
    console.log("无效的Solana地址");
}
