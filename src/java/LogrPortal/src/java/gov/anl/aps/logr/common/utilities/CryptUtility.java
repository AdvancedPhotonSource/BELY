/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */

import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.security.spec.InvalidKeySpecException;
import java.util.Random;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.util.Base64;
import java.util.Arrays;

/**
 * Utility class for encrypting and verifying passwords.
 */
public class CryptUtility{

    private static final String SecretKeyFactoryType = "PBKDF2WithHmacSHA512";
    private static final int Pbkdf2Iterations = 25000;
    private static final int Pbkdf2KeyLengthInBits = 512;
    private static final int SaltLengthInBytes = 16;
    private static final char[] SaltCharset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".toCharArray();
    private static final String SaltDelimiter = "$";

//    private static final Logger logger = LogManager.getLogger(CryptUtility.class.getName());
    
    private static final SecureRandom secureRandom = new SecureRandom(); 
    private static final Base64.Encoder base64Encoder = Base64.getUrlEncoder(); 

    /**
     * Generate random string.
     *
     * @param characterSet set to draw characters from
     * @param length string length
     * @return generated string
     */
    public static String randomString(char[] characterSet, int length) {
        Random random = new SecureRandom();
        char[] result = new char[length];
        for (int i = 0; i < result.length; i++) {
            // picks a random index out of character set > random character
            int randomCharIndex = random.nextInt(characterSet.length);
            result[i] = characterSet[randomCharIndex];
        }
        return new String(result);
    }
    
    public static String generateSessionToken() {
        byte[] randomBytes = new byte[24];
        secureRandom.nextBytes(randomBytes);
        return base64Encoder.encodeToString(randomBytes);
    }

    /**
     * Encrypt password using PBKDF2 key derivation function.
     *
     * @param password input password
     * @return encrypted password
     */
    public static String cryptPasswordWithPbkdf2(String password) {
        String salt = randomString(SaltCharset, SaltLengthInBytes);
        return saltAndCryptPasswordWithPbkdf2(password, salt);
    }

    /**
     * Apply salt string and encrypt password using PBKDF2 standard.
     *
     * @param password input password
     * @param salt salt string
     * @return encrypted password
     */
    public static String saltAndCryptPasswordWithPbkdf2(String password, String salt) {
        char[] passwordChars = password.toCharArray();
        byte[] saltBytes = salt.getBytes();

        PBEKeySpec spec = new PBEKeySpec(
                passwordChars,
                saltBytes,
                Pbkdf2Iterations,
                Pbkdf2KeyLengthInBits
        );
        SecretKeyFactory key;
        try {
            key = SecretKeyFactory.getInstance(SecretKeyFactoryType);
            byte[] hashedPassword = key.generateSecret(spec).getEncoded();
            String encodedPassword = Base64.getEncoder().encodeToString(hashedPassword);
            String encodedSalt = Base64.getEncoder().encodeToString(saltBytes);
            return SaltDelimiter+"pbkdf2-sha512"+SaltDelimiter+"25000"+SaltDelimiter+encodedSalt + SaltDelimiter + encodedPassword;
        } catch (NoSuchAlgorithmException | InvalidKeySpecException ex) {
            // Should not happen
//            logger.error("Password cannot be crypted: " + ex);
        }
        return null;
    }

    /**
     * Apply salt string and encrypt password using PBKDF2 standard.
     *
     * @param password input password
     * @param salt salt string
     * @return encrypted password
     */
    public static String OnlyCryptPasswordWithPbkdf2(String password, String salt) {
        char[] passwordChars = password.toCharArray();
        byte[] saltBytes = (Base64.getDecoder().decode(salt));
//		logger.error("calling OnlyCryp...: " + password + "."+salt);
        PBEKeySpec spec = new PBEKeySpec(
                passwordChars,
                saltBytes,
                Pbkdf2Iterations,
                Pbkdf2KeyLengthInBits
        );
        SecretKeyFactory key;
        try {
            key = SecretKeyFactory.getInstance(SecretKeyFactoryType);
            byte[] hashedPassword = key.generateSecret(spec).getEncoded();
            String encodedPassword = Base64.getEncoder().encodeToString(hashedPassword);
            return encodedPassword;
        } catch (NoSuchAlgorithmException | InvalidKeySpecException ex) {
            // Should not happen
//            logger.error("Password cannot be crypted: " + ex);
        }
        return null;
    }


    /**
     * Verify encrypted password.
     *
     * @param password password to be verified
     * @param cryptedPassword original encrypted password
     * @return true if passwords match, false otherwise
     */
    public static boolean verifyPasswordWithPbkdf2(String password, String cryptedPassword) {
        int saltBegin, saltEnd,i;
        saltBegin=1;
        for (i=0;i<2;i++)
             saltBegin = cryptedPassword.indexOf(SaltDelimiter,saltBegin) + 1;
        saltEnd = cryptedPassword.indexOf(SaltDelimiter,saltBegin);
        
//        logger.error("password:"+cryptedPassword);
        String salt = cryptedPassword.substring(saltBegin, saltEnd);
        String pw=cryptedPassword.substring(saltEnd+1);
//        logger.error("saltend:"+,saltEnd+ "T",saltBegin + pw)
        String epw=OnlyCryptPasswordWithPbkdf2(password, salt);
//        logger.error("salt:"+salt + " hash$" + pw + "new: " + epw );
        return pw.equals(epw);
    }

    /*
     * Main method, used for simple testing.
     * 
     * @param args main arguments
     */
    public static void main(String[] args) {
        String password = args[0];
        System.out.println("Original password: " + password);
        String cryptedPassword = cryptPasswordWithPbkdf2(password);
        System.out.println("Crypted password: " + cryptedPassword);
        System.out.println("Verified: " + verifyPasswordWithPbkdf2(password, cryptedPassword));
        
    }
}
