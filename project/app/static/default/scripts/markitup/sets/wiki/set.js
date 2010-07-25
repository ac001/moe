// -------------------------------------------------------------------
// markItUp!
// -------------------------------------------------------------------
// Copyright (C) 2008 Jay Salvat
// http://markitup.jaysalvat.com/
// -------------------------------------------------------------------
// Mediawiki Wiki tags example
// -------------------------------------------------------------------
// Feel free to add more tags
// -------------------------------------------------------------------
mySettings = {
    previewParserPath:	'', // path to your Wiki parser
    onShiftEnter:		{keepDefault:false, replaceWith:'\n\n'},
    markupSet: [
        {name:'Heading 1', key:'1', openWith:'= ', placeHolder:'Your title here...' },
        {name:'Heading 2', key:'2', openWith:'== ', placeHolder:'Your title here...' },
        {name:'Heading 3', key:'3', openWith:'=== ', placeHolder:'Your title here...' },
        {name:'Heading 4', key:'4', openWith:'==== ', placeHolder:'Your title here...' },
        {name:'Heading 5', key:'5', openWith:'===== ', placeHolder:'Your title here...' },
        {name:'Heading 6', key:'6', openWith:'====== ', placeHolder:'Your title here...' },
        {separator:'---------------' },
        {name:'Bold', key:'B', openWith:"**", closeWith:"**"},
        {name:'Italic', key:'I', openWith:"//", closeWith:"//"},
        {separator:'---------------' },
        {name:'Bulleted list', openWith:'(!(* |!|*)!)'},
        {name:'Numbered list', openWith:'(!(# |!|#)!)'},
        {separator:'---------------' },
        {name:'Preformatted', key:'P', openWith:'{{{', closeWith:'}}}'},
        {name:'Highlighted code', key:'H', openWith:'(!(<<code [![Language:!:python]!]>>|!|<<code>>)!)', closeWith:'<</code>>'},
        {separator:'---------------' },
        {name:'Link', key:"L", openWith:"[[[![Link]!]|", closeWith:']]', placeHolder:'Your text to link here...' },
    ]
}