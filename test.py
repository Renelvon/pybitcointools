import json
import os
import random
import sys
import unittest

import bitcoin.ripemd as ripemd
from bitcoin import *

argv = sys.argv + ['y']*15

def TestECCArithmetic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print 'Starting ECC arithmetic tests'

    def test_all(self):
        for i in range(8):
            print '### Round %d' % (i+1)
            x, y = random.randrange(2**256), random.randrange(2**256)
            self.assertEqual(
                multiply(multiply(G, x), y)[0],
                multiply(multiply(G, y), x)[0]
            )
            self.assertEqual(
                add_pubkeys(multiply(G, x), multiply(G, y))[0],
                multiply(G, add_privkeys(x, y))[0]
            )

            hx, hy = encode(x % N, 16, 64), encode(y % N, 16, 64)
            self.assertEqual(
                multiply(multiply(G, hx), hy)[0],
                multiply(multiply(G, hy), hx)[0]
            )
            self.assertEqual(
                add_pubkeys(multiply(G, hx), multiply(G, hy))[0],
                multiply(G, add_privkeys(hx, hy))[0]
            )

            self.assertEqual(
                b58check_to_hex(pubtoaddr(privtopub(x))),
                b58check_to_hex(pubtoaddr(multiply(G, hx), 23))
            )

            p = privtopub(sha256(str(x)))
            if i % 2 == 1:
                p = changebase(p, 16, 256)
            self.assertEqual(p, decompress(compress(p)))

            self.assertEqual(G[0], multiply(divide(G, x), x)[0])


def TestElectrumWalletInternalConsistency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print 'Starting Electrum wallet internal consistency tests'

    def test_all(self):
        for i in range(3):
            seed = sha256(str(random.randrange(2**40)))[:32]
            mpk = electrum_mpk(seed)
            for i in range(5):
                pk = electrum_privkey(seed, i)
                pub = electrum_pubkey((mpk, seed)[i % 2], i)
                pub2 = privtopub(pk)
                self.assertEqual(
                    pub,
                    pub2,
                    'Does not match! Details:\nseed: %s\nmpk: %s\npriv: %s\npub: %s\npub2: %s' % (
                        seed, mpk, priv, pub, pub2
                    )
                )


if argv[3] == 'y':
    # Requires Electrum
    wallet = "/tmp/tempwallet_"+str(random.randrange(2**40))
    print "Starting wallet tests with: "+wallet
    os.popen('echo "\n\n\n\n\n\n" | electrum -w %s create' % wallet).read()
    seed = str(json.loads(os.popen("electrum -w %s getseed" % wallet).read())['seed'])
    addies = json.loads(os.popen("electrum -w %s listaddresses" % wallet).read())
    for i in range(5):
        if addies[i] != electrum_address(seed, i, 0):
            print "Address does not match!!!, seed: %s, i: %d" % (seed, i)

    print "Electrum-style signing and verification tests, against actual Electrum"
    for i in range(8):
        alphabet = "1234567890qwertyuiopasdfghjklzxcvbnm"
        msg = ''.join([random.choice(alphabet) for i in range(random.randrange(20, 200))])
        addy = random.choice(addies)
        wif = os.popen('electrum -w %s dumpprivkey %s' % (wallet, addy)).readlines()[-2].replace('"', '').strip()
        priv = b58check_to_hex(wif)
        pub = privtopub(priv)

        sig = os.popen('electrum -w %s signmessage %s %s' % (wallet, addy, msg)).readlines()[-1].strip()
        verified = ecdsa_verify(msg, sig, pub)
        print "Verified" if verified else "Verification error"
        rec = ecdsa_recover(msg, sig)
        if pub == rec:
            print "Recovery successful"
        if pub != rec or not verified:
            print "msg: "+msg
            print "sig: "+sig
            print "priv: "+priv
            print "addy: "+addy
        if pub != rec:
            print "Recovery error"
            print "original  pub: "+pub, hex_to_point(pub)[1]
            print "recovered pub: "+rec

        mysig = ecdsa_sign(msg, priv)
        v = os.popen('electrum -w %s verifymessage %s %s %s' % (wallet, addy, sig, msg)).read()
        print v


def TestTransactionSignVerify(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print "Transaction-style signing and verification tests"

    def test_all(self):
        alphabet = "1234567890qwertyuiopasdfghjklzxcvbnm"
        for i in range(10):
            msg = ''.join([random.choice(alphabet) for i in range(random.randrange(20, 200))])
            priv = sha256(str(random.randrange(2**256)))
            pub = privtopub(priv)
            sig = ecdsa_tx_sign(msg, priv)
            self.assertTrue(
                ecdsa_tx_verify(msg, sig, pub),
                "Verification error"
            )

            self.assertIn(
                pub,
                ecdsa_tx_recover(msg, sig),
                "Recovery failed"
            )


def TestSerialize(unittest.TestCase):

    def test_serialize(self):
        tx = '0100000001239f932c780e517015842f3b02ff765fba97f9f63f9f1bc718b686a56ed9c73400000000fd5d010047304402200c40fa58d3f6d5537a343cf9c8d13bc7470baf1d13867e0de3e535cd6b4354c802200f2b48f67494835b060d0b2ff85657d2ba2d9ea4e697888c8cb580e8658183a801483045022056f488c59849a4259e7cef70fe5d6d53a4bd1c59a195b0577bd81cb76044beca022100a735b319fa66af7b178fc719b93f905961ef4d4446deca8757a90de2106dd98a014cc95241046c7d87fd72caeab48e937f2feca9e9a4bd77f0eff4ebb2dbbb9855c023e334e188d32aaec4632ea4cbc575c037d8101aec73d029236e7b1c2380f3e4ad7edced41046fd41cddf3bbda33a240b417a825cc46555949917c7ccf64c59f42fd8dfe95f34fae3b09ed279c8c5b3530510e8cca6230791102eef9961d895e8db54af0563c410488d618b988efd2511fc1f9c03f11c210808852b07fe46128c1a6b1155aa22cdf4b6802460ba593db2d11c7e6cbe19cedef76b7bcabd05d26fd97f4c5a59b225053aeffffffff0310270000000000001976a914a89733100315c37d228a529853af341a9d290a4588ac409c00000000000017a9142b56f9a4009d9ff99b8f97bea4455cd71135f5dd87409c00000000000017a9142b56f9a4009d9ff99b8f97bea4455cd71135f5dd8700000000'
        self.assertEqual(
            serialize(deserialize(tx)),
            tx,
            "Serialize roundtrip failed"
        )

        def test_serialize_script(self):
            script = '47304402200c40fa58d3f6d5537a343cf9c8d13bc7470baf1d13867e0de3e535cd6b4354c802200f2b48f67494835b060d0b2ff85657d2ba2d9ea4e697888c8cb580e8658183a801483045022056f488c59849a4259e7cef70fe5d6d53a4bd1c59a195b0577bd81cb76044beca022100a735b319fa66af7b178fc719b93f905961ef4d4446deca8757a90de2106dd98a014cc95241046c7d87fd72caeab48e937f2feca9e9a4bd77f0eff4ebb2dbbb9855c023e334e188d32aaec4632ea4cbc575c037d8101aec73d029236e7b1c2380f3e4ad7edced41046fd41cddf3bbda33a240b417a825cc46555949917c7ccf64c59f42fd8dfe95f34fae3b09ed279c8c5b3530510e8cca6230791102eef9961d895e8db54af0563c410488d618b988efd2511fc1f9c03f11c210808852b07fe46128c1a6b1155aa22cdf4b6802460ba593db2d11c7e6cbe19cedef76b7bcabd05d26fd97f4c5a59b225053ae'
        self.assertEqual(
            serialize_script(deserialize_script(script)),
            script,
            "Script serialize roundtrip failed"
        )


def TestTransaction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print "Attempting transaction creation"

    # FIXME: I don't know how to write this as a unit test.
    # What should be asserted?
    def test_all(self):
        privs = [sha256(str(random.randrange(2**256))) for x in range(4)]
        pubs = [privtopub(priv) for priv in privs]
        addresses = [pubtoaddr(pub) for pub in pubs]
        mscript = mk_multisig_script(pubs[1:], 2, 3)
        msigaddr = p2sh_scriptaddr(mscript)
        tx = mktx(['01'*32+':1', '23'*32+':2'], [msigaddr+':20202', addresses[0]+':40404'])
        tx1 = sign(tx, 1, privs[0])
        sig1 = multisign(tx, 0, mscript, privs[1])
        print "Verifying sig1:", verify_tx_input(tx1, 0, mscript, sig1, pubs[1])
        sig3 = multisign(tx, 0, mscript, privs[3])
        print "Verifying sig3:", verify_tx_input(tx1, 0, mscript, sig3, pubs[3])
        tx2 = apply_multisignatures(tx1, 0, mscript, [sig1, sig3])
        print "Outputting transaction: ", tx2


def TestDeterministicGenerate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print "Beginning RFC6979 deterministic signing tests"

    def test_all(self):
        # Created with python-ecdsa 0.9
        # Code to make your own vectors:
        # class gen:
        #     def order(self): return 115792089237316195423570985008687907852837564279074904382605163141518161494337
        # dummy = gen()
        # for i in range(10): ecdsa.rfc6979.generate_k(dummy, i, hashlib.sha256, hashlib.sha256(str(i)).digest())
        test_vectors = [
            32783320859482229023646250050688645858316445811207841524283044428614360139869L,
            109592113955144883013243055602231029997040992035200230706187150761552110229971L,
            65765393578006003630736298397268097590176526363988568884298609868706232621488L,
            85563144787585457107933685459469453513056530050186673491900346620874099325918L,
            99829559501561741463404068005537785834525504175465914981205926165214632019533L,
            7755945018790142325513649272940177083855222863968691658328003977498047013576L,
            81516639518483202269820502976089105897400159721845694286620077204726637043798L,
            52824159213002398817852821148973968315579759063230697131029801896913602807019L,
            44033460667645047622273556650595158811264350043302911918907282441675680538675L,
            32396602643737403620316035551493791485834117358805817054817536312402837398361L
        ]

        for i, ti in enumerate(test_vectors):
            mine = deterministic_generate_k(bin_sha256(str(i)), encode(i, 256, 32))
            self.assertEqual(
                ti,
                mine,
                "Test vector does not match. Details:\n%s\n%s" % (
                    ti,
                    mine
                )
            )


def TestBIP0032(unittest.TestCase):
    """See: https://en.bitcoin.it/wiki/BIP_0032"""
    @classmethod
    def setUpClass(cls):
        print "Beginning BIP0032 tests"

    def _full_derive(self, key, chain):
        if len(chain) == 0:
            return key
        elif chain[0] == 'pub':
            return self._full_derive(bip32_privtopub(key), chain[1:])
        else:
            return self._full_derive(bip32_ckd(key, chain[0]), chain[1:])

    def test_all(self):
        test_vectors = [
            [[], 'xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi'],
            [['pub'], 'xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8'],
            [[2**31], 'xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7'],
            [[2**31, 1], 'xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs'],
            [[2**31, 1, 2**31 + 2], 'xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4mLTj34bhnZX7UiM'],
            [[2**31, 1, 2**31 + 2, 'pub', 2, 1000000000], 'xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTvXEYBVPamhGW6cFJodrTHy']
        ]

        mk = bip32_master_key('000102030405060708090a0b0c0d0e0f'.decode('hex'))

    for tv in test_vectors:
        left, right = self._full_derive(mk, tv[0]), tv[1]
        self.assertEqual(
            left,
            right,
            "Test vector does not match. Details: \n%s\n%s\n\%s" % (
                tv[0],
                [x.encode('hex') if isinstance(x, str) else x for x in bip32_deserialize(left)],
                [x.encode('hex') if isinstance(x, str) else x for x in bip32_deserialize(right)],
            )
        )


def TestStartingAddressAndScriptGenerationConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print "Starting address and script generation consistency tests"

    def test_all(self):
        for i in range(5):
            a = privtoaddr(random_key())
            self.assertEqual(a, script_to_address(address_to_script(a)))
            b = privtoaddr(random_key(), 5)
            self.assertEqual(b, script_to_address(address_to_script(b)))


def TestRipeMD160PythonBackup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print 'Testing the pure python backup for ripemd160'

    def test_all(self):
        strvec = [
            '',
            'The quick brown fox jumps over the lazy dog',
            'The quick brown fox jumps over the lazy cog',
            'Nobody inspects the spammish repetition'
        ]

        target = [
            '9c1185a5c5e9fc54612808977ee8f548b2258d31',
            '37f332f68db77bd9d7edd4969571ad671cf9dd3b',
            '132072df690933835eb8b6ad0b77e7b6f14acad7',
            'cc4a5ce1b3df48aec5d22d1f16b894a0b894eccc'
        ]

        hash160target = [
            'b472a266d0bd89c13706a4132ccfb16f7c3b9fcb',
            '0e3397b4abc7a382b3ea2365883c3c7ca5f07600',
            '53e0dacac5249e46114f65cb1f30d156b14e0bdc',
            '1c9b7b48049a8f98699bca22a5856c5ef571cd68'
        ]

        for i, s in enumerate(strvec):
            digest = ripemd.RIPEMD160(s).digest()
            hash160digest = ripemd.RIPEMD160(bin_sha256(s).digest())
            self.assertEqual(digest.encode('hex'), target[i])
            self.assertEqual(hash160digest.encode('hex'), hash160target[i])
            self.assertEqual(bin_hash160(s).encode('hex'), hash160target[i])
            self.assertEqual(hash160(s), hash160target[i])


def TestScriptVsAddressOutputs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print 'Testing script vs address outputs'

    def test_all(self):
        addr0 = '1Lqgj1ThNfwLgHMp5qJUerYsuUEm8vHmVG'
        script0 = '76a914d99f84267d1f90f3e870a5e9d2399918140be61d88ac'
        addr1 = '31oSGBBNrpCiENH3XMZpiP6GTC4tad4bMy'
        script1 = 'a9140136d001619faba572df2ef3d193a57ad29122d987'

        inputs = [{
            'output': 'cd6219ea108119dc62fce09698b649efde56eca7ce223a3315e8b431f6280ce7:0',
            'value': 158000
        }]

        outputs = [
            [{'address': addr0, 'value': 1000}, {'address': addr1, 'value': 2000}],
            [{'script': script0, 'value': 1000}, {'address': addr1, 'value': 2000}],
            [{'address': addr0, 'value': 1000}, {'script': script1, 'value': 2000}],
            [{'script': script0, 'value': 1000}, {'script': script1, 'value': 2000}],
            [addr0 + ':1000', addr1 + ':2000'],
            [script0 + ':1000', addr1 + ':2000'],
            [addr0 + ':1000', script1 + ':2000'],
            [script0 + ':1000', script1 + ':2000']
        ]

        for outs in outputs:
            tx_struct = deserialize(mktx(inputs, outs))
            self.assertEqual(tx_struct['outs'], outputs[3])

if __name__ == '__main__':
    unittest.main()
