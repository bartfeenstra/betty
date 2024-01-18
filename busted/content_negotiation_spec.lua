local cone = require('../betty/extension/nginx/assets/content_negotiation')

describe('negotiate', function ()
    it('nil header, with nil available, should not return', function ()
        assert.is_nil(cone.negotiate(nil, nil))
    end)

    it('nil header, with none available, should not return', function ()
        assert.is_nil(cone.negotiate(nil, {}))
    end)

    it('empty header, with nil available, should not return', function ()
        assert.is_nil(cone.negotiate('', nil))
    end)

    it('empty header, with none available, should not return', function ()
        assert.is_nil(cone.negotiate('', {}))
    end)

    it('empty header containing spaces, with none available, should not return', function ()
        assert.is_nil(cone.negotiate(' ', {}))
    end)

    it('empty header containing tabs, with none available, should not return', function ()
        assert.is_nil(cone.negotiate('	', {}))
    end)

    it('empty header, with one available, should return the default available', function ()
        assert.are.equal('apples', cone.negotiate('', {'apples'}))
    end)

    it('empty header, with multiple available, should return the default available', function ()
        assert.are.equal('apples', cone.negotiate('', {'apples', 'oranges', 'bananas'}))
    end)

    it('header with multiple, with multiple others available, should return the default available', function ()
        assert.are.equal('apples', cone.negotiate('uk,fr,la', {'apples', 'oranges', 'bananas'}))
    end)

    it('header with one value, with none available, should not return', function ()
        assert.is_nil(cone.negotiate('apples', {}))
    end)

    it('header with multiple values, with none available, should not return', function ()
        assert.is_nil(cone.negotiate('apples,oranges,bananas', {}))
    end)

    it('header with one value, with one available, should not return', function ()
        assert.are.equal('apples', cone.negotiate('apples', {'apples'}))
    end)

    it('header with one value with a default quality, being the last available, should return the one header value', function ()
        assert.are.equal('bananas', cone.negotiate('bananas', {'apples', 'oranges', 'bananas'}))
    end)

    it('header with one value with an explicit quality, being the last available, should return the one header value', function ()
        assert.are.equal('bananas', cone.negotiate('bananas;q=0.5', {'apples', 'oranges', 'bananas'}))
    end)

    it('header with one value with an unacceptable quality, being the last available, should return the one header value', function ()
        assert.are.equal('oranges', cone.negotiate('apples;q=0', {'apples', 'oranges', 'bananas'}))
    end)

    it('header with multiple values and whitespace, should return the preferred header value', function ()
        assert.are.equal('bananas', cone.negotiate('bananas	, oranges', {'apples', 'oranges', 'bananas'}))
    end)
end)
