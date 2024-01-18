local Cone = {}

function Cone.negotiate(header, available_values)
    if available_values == nil or available_values == {} then
        return nil
    end

    if header == nil or header == '' then
        return available_values[1]
    end

    header = header:gsub('%s+', '')

    acceptable_values = {}
    unacceptable_values = {}
    for qualified_value in header:gmatch('([^,]+)') do
        value, quality = Cone.parse_qualified_value(qualified_value)
        if quality == 0 then
            table.insert(unacceptable_values, value)
        else
            table.insert(acceptable_values, { value, quality})
        end
    end
    -- Sort the values by quality in descending order.
    table.sort(acceptable_values, function(a, b) return a[2] > b[2] end)

    for _, qualified_acceptable_value in ipairs(acceptable_values) do
        acceptable_value = qualified_acceptable_value[1]
        for _, available_value in pairs(available_values) do
            if acceptable_value == available_value then
                return acceptable_value
            end
        end
    end

    for _, available_value in ipairs(available_values) do
        if not Cone._contains(available_value, unacceptable_values) then
            return available_value
        end
    end

    return available_values[1]
end

function Cone.parse_qualified_value(qualified_value)
    if qualified_value:find(';q=') then
        value, quality = qualified_value:match("(.*)%;q=(.*)")
        quality = tonumber(quality)
    else
        value = qualified_value
        quality = 1
    end
    return value, quality
end

function Cone._contains(needle, haystack)
    for _, haystack_value in pairs(haystack) do
        if haystack_value == needle then
            return true
        end
    end
    return false
end

return Cone
