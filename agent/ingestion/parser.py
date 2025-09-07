"""
Code parsing functionality using Tree-sitter.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from tree_sitter import Language, Node, Parser

from agent.core.models import Edge, EdgeType, ParseUnit, Symbol, SymbolType

# Load language libraries
try:
    from tree_sitter_python import language as python_language
    PYTHON_LANGUAGE = Language(python_language())
except ImportError:
    logger.warning("Python tree-sitter language not available")
    PYTHON_LANGUAGE = None

try:
    from tree_sitter_typescript import language as ts_language
    TYPESCRIPT_LANGUAGE = Language(ts_language())
except ImportError:
    logger.warning("TypeScript tree-sitter language not available")
    TYPESCRIPT_LANGUAGE = None


def parse_file(parse_unit: ParseUnit) -> ParseUnit:
    """
    Parse a file and extract symbols and relationships.
    
    Args:
        parse_unit: Parse unit with file content
        
    Returns:
        Updated parse unit with AST, symbols, and edges
    """
    logger.debug(f"Parsing file: {parse_unit.path}")
    
    # Get the appropriate language parser
    language = get_tree_sitter_language(parse_unit.language)
    if not language:
        logger.warning(f"No parser available for language: {parse_unit.language}")
        return parse_unit
    
    # Create parser
    parser = Parser()
    parser.set_language(language)
    
    # Parse the content
    tree = parser.parse(bytes(parse_unit.content, "utf8"))
    
    # Store the AST
    parse_unit.ast = tree.root_node.to_dict()
    
    # Extract symbols and edges
    symbols, edges = extract_symbols_and_edges(
        tree.root_node, 
        parse_unit.path, 
        parse_unit.language,
        parse_unit.repo_id
    )
    
    parse_unit.symbols = symbols
    parse_unit.edges = edges
    
    logger.debug(f"Extracted {len(symbols)} symbols and {len(edges)} edges from {parse_unit.path}")
    return parse_unit


def get_tree_sitter_language(language):
    """
    Get the Tree-sitter language object for a given language.
    
    Args:
        language: Language enum value
        
    Returns:
        Tree-sitter Language object or None if not available
    """
    if language.value == "python":
        return PYTHON_LANGUAGE
    elif language.value in ["typescript", "javascript"]:
        return TYPESCRIPT_LANGUAGE
    else:
        logger.warning(f"Unsupported language: {language}")
        return None


def extract_symbols_and_edges(
    root_node: Node, 
    file_path: str, 
    language: str,
    repo_id: str
) -> Tuple[List[Symbol], List[Edge]]:
    """
    Extract symbols and edges from a syntax tree.
    
    Args:
        root_node: Root node of the syntax tree
        file_path: Path to the file
        language: Programming language
        repo_id: Repository ID
        
    Returns:
        Tuple of (symbols, edges)
    """
    symbols = []
    edges = []
    
    # Language-specific extraction
    if language == "python":
        symbols, edges = extract_python_symbols_and_edges(root_node, file_path, repo_id)
    elif language in ["typescript", "javascript"]:
        symbols, edges = extract_typescript_symbols_and_edges(root_node, file_path, repo_id)
    
    return symbols, edges


def extract_python_symbols_and_edges(
    root_node: Node, 
    file_path: str, 
    repo_id: str
) -> Tuple[List[Symbol], List[Edge]]:
    """
    Extract symbols and edges from a Python syntax tree.
    
    Args:
        root_node: Root node of the Python syntax tree
        file_path: Path to the file
        repo_id: Repository ID
        
    Returns:
        Tuple of (symbols, edges)
    """
    symbols = []
    edges = []
    
    # Query for function definitions
    function_nodes = root_node.children_by_type("function_definition")
    for node in function_nodes:
        symbol = extract_python_function(node, file_path, repo_id)
        if symbol:
            symbols.append(symbol)
    
    # Query for class definitions
    class_nodes = root_node.children_by_type("class_definition")
    for node in class_nodes:
        class_symbol = extract_python_class(node, file_path, repo_id)
        if class_symbol:
            symbols.append(class_symbol)
            
            # Extract methods within the class
            method_nodes = node.children_by_type("function_definition")
            for method_node in method_nodes:
                method_symbol = extract_python_function(method_node, file_path, repo_id, parent_id=class_symbol.id)
                if method_symbol:
                    symbols.append(method_symbol)
                    
                    # Create edge from class to method
                    edge = Edge(
                        source_id=class_symbol.id,
                        target_id=method_symbol.id,
                        type=EdgeType.CONTAINS,
                        repo_id=repo_id
                    )
                    edges.append(edge)
    
    # Query for imports
    import_nodes = root_node.children_by_type("import_statement")
    for node in import_nodes:
        import_edges = extract_python_imports(node, symbols, repo_id)
        edges.extend(import_edges)
    
    # Query for function calls
    call_nodes = root_node.children_by_type("call")
    for node in call_nodes:
        call_edges = extract_python_calls(node, symbols, repo_id)
        edges.extend(call_edges)
    
    return symbols, edges


def extract_python_function(
    node: Node, 
    file_path: str, 
    repo_id: str,
    parent_id: Optional[str] = None
) -> Optional[Symbol]:
    """
    Extract a function symbol from a Python function definition node.
    
    Args:
        node: Function definition node
        file_path: Path to the file
        repo_id: Repository ID
        parent_id: ID of the parent symbol (e.g., class)
        
    Returns:
        Symbol object or None if extraction failed
    """
    try:
        # Get function name
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
            
        name = name_node.text.decode("utf8")
        
        # Get function parameters
        parameters_node = node.child_by_field_name("parameters")
        parameters = []
        if parameters_node:
            for param_node in parameters_node.children:
                if param_node.type == "identifier":
                    parameters.append(param_node.text.decode("utf8"))
        
        # Get docstring
        docstring = None
        body_node = node.child_by_field_name("body")
        if body_node and len(body_node.children) > 0:
            first_stmt = body_node.children[0]
            if first_stmt.type == "expression_statement":
                expr_node = first_stmt.children[0]
                if expr_node.type == "string":
                    docstring = expr_node.text.decode("utf8")
                    # Remove quotes
                    if docstring.startswith(('"""', "'''")):
                        docstring = docstring[3:-3]
                    elif docstring.startswith(('"', "'")):
                        docstring = docstring[1:-1]
        
        # Create symbol
        symbol_type = SymbolType.METHOD if parent_id else SymbolType.FUNCTION
        symbol = Symbol(
            name=name,
            type=symbol_type,
            file_path=file_path,
            language=Language.PYTHON,
            start_line=node.start_point[0] + 1,  # Convert to 1-based
            end_line=node.end_point[0] + 1,
            start_column=node.start_point[1] + 1,
            end_column=node.end_point[1] + 1,
            docstring=docstring,
            signature=f"{name}({', '.join(parameters)})",
            parent_id=parent_id,
            metadata={
                "parameters": parameters,
            },
            repo_id=repo_id
        )
        
        return symbol
    except Exception as e:
        logger.error(f"Error extracting Python function: {e}")
        return None


def extract_python_class(
    node: Node, 
    file_path: str, 
    repo_id: str
) -> Optional[Symbol]:
    """
    Extract a class symbol from a Python class definition node.
    
    Args:
        node: Class definition node
        file_path: Path to the file
        repo_id: Repository ID
        
    Returns:
        Symbol object or None if extraction failed
    """
    try:
        # Get class name
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
            
        name = name_node.text.decode("utf8")
        
        # Get superclasses
        superclasses = []
        arguments_node = node.child_by_field_name("arguments")
        if arguments_node:
            for arg_node in arguments_node.children:
                if arg_node.type == "identifier":
                    superclasses.append(arg_node.text.decode("utf8"))
        
        # Get docstring
        docstring = None
        body_node = node.child_by_field_name("body")
        if body_node and len(body_node.children) > 0:
            first_stmt = body_node.children[0]
            if first_stmt.type == "expression_statement":
                expr_node = first_stmt.children[0]
                if expr_node.type == "string":
                    docstring = expr_node.text.decode("utf8")
                    # Remove quotes
                    if docstring.startswith(('"""', "'''")):
                        docstring = docstring[3:-3]
                    elif docstring.startswith(('"', "'")):
                        docstring = docstring[1:-1]
        
        # Create symbol
        symbol = Symbol(
            name=name,
            type=SymbolType.CLASS,
            file_path=file_path,
            language=Language.PYTHON,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            start_column=node.start_point[1] + 1,
            end_column=node.end_point[1] + 1,
            docstring=docstring,
            parent_id=None,
            metadata={
                "superclasses": superclasses,
            },
            repo_id=repo_id
        )
        
        return symbol
    except Exception as e:
        logger.error(f"Error extracting Python class: {e}")
        return None


def extract_python_imports(
    node: Node, 
    symbols: List[Symbol], 
    repo_id: str
) -> List[Edge]:
    """
    Extract import edges from a Python import statement node.
    
    Args:
        node: Import statement node
        symbols: List of symbols in the file
        repo_id: Repository ID
        
    Returns:
        List of import edges
    """
    edges = []
    
    try:
        # Handle "import" statements
        if node.children and node.children[0].type == "import":
            # Find all imported modules
            for child in node.children:
                if child.type == "dotted_name":
                    module_name = child.text.decode("utf8")
                    
                    # Create edges to all functions in the file (this is a simplification)
                    for symbol in symbols:
                        if symbol.type in [SymbolType.FUNCTION, SymbolType.CLASS]:
                            edge = Edge(
                                source_id=symbol.id,
                                target_id=None,  # External module, no target ID
                                type=EdgeType.IMPORTS,
                                metadata={"module": module_name},
                                repo_id=repo_id
                            )
                            edges.append(edge)
        
        # Handle "from" import statements
        elif node.children and node.children[0].type == "from":
            # Extract module name
            module_node = None
            for child in node.children:
                if child.type == "dotted_name":
                    module_node = child
                    break
            
            if module_node:
                module_name = module_node.text.decode("utf8")
                
                # Find imported names
                import_list = None
                for child in node.children:
                    if child.type == "import_list":
                        import_list = child
                        break
                
                if import_list:
                    for child in import_list.children:
                        if child.type == "dotted_name" or child.type == "identifier":
                            imported_name = child.text.decode("utf8")
                            
                            # Find matching symbols in the file
                            for symbol in symbols:
                                if symbol.name == imported_name:
                                    edge = Edge(
                                        source_id=symbol.id,
                                        target_id=None,  # External module, no target ID
                                        type=EdgeType.IMPORTS,
                                        metadata={"module": module_name, "name": imported_name},
                                        repo_id=repo_id
                                    )
                                    edges.append(edge)
    except Exception as e:
        logger.error(f"Error extracting Python imports: {e}")
    
    return edges


def extract_python_calls(
    node: Node, 
    symbols: List[Symbol], 
    repo_id: str
) -> List[Edge]:
    """
    Extract call edges from a Python call node.
    
    Args:
        node: Call node
        symbols: List of symbols in the file
        repo_id: Repository ID
        
    Returns:
        List of call edges
    """
    edges = []
    
    try:
        # Get the function being called
        function_node = node.child_by_field_name("function")
        if not function_node:
            return edges
        
        # Handle different types of function references
        if function_node.type == "identifier":
            function_name = function_node.text.decode("utf8")
            
            # Find matching symbols in the file
            for symbol in symbols:
                if symbol.name == function_name and symbol.type in [SymbolType.FUNCTION, SymbolType.METHOD]:
                    # This is a simplification - we should check the context to determine the caller
                    # For now, we'll assume the call is from the first function in the file
                    caller_symbol = None
                    for s in symbols:
                        if s.type in [SymbolType.FUNCTION, SymbolType.METHOD]:
                            caller_symbol = s
                            break
                    
                    if caller_symbol:
                        edge = Edge(
                            source_id=caller_symbol.id,
                            target_id=symbol.id,
                            type=EdgeType.CALLS,
                            repo_id=repo_id
                        )
                        edges.append(edge)
        
        # Handle attribute access (e.g., object.method())
        elif function_node.type == "attribute":
            # Extract the method name
            attribute_node = function_node.child_by_field_name("attribute")
            if attribute_node and attribute_node.type == "identifier":
                method_name = attribute_node.text.decode("utf8")
                
                # Find matching method symbols in the file
                for symbol in symbols:
                    if symbol.name == method_name and symbol.type == SymbolType.METHOD:
                        # This is a simplification - we should check the context to determine the caller
                        # For now, we'll assume the call is from the first function in the file
                        caller_symbol = None
                        for s in symbols:
                            if s.type in [SymbolType.FUNCTION, SymbolType.METHOD]:
                                caller_symbol = s
                                break
                        
                        if caller_symbol:
                            edge = Edge(
                                source_id=caller_symbol.id,
                                target_id=symbol.id,
                                type=EdgeType.CALLS,
                                repo_id=repo_id
                            )
                            edges.append(edge)
    except Exception as e:
        logger.error(f"Error extracting Python calls: {e}")
    
    return edges


def extract_typescript_symbols_and_edges(
    root_node: Node, 
    file_path: str, 
    repo_id: str
) -> Tuple[List[Symbol], List[Edge]]:
    """
    Extract symbols and edges from a TypeScript syntax tree.
    
    Args:
        root_node: Root node of the TypeScript syntax tree
        file_path: Path to the file
        repo_id: Repository ID
        
    Returns:
        Tuple of (symbols, edges)
    """
    # This is a placeholder implementation
    # In a real implementation, we would extract TypeScript-specific symbols and edges
    symbols = []
    edges = []
    
    # Query for function declarations
    function_nodes = root_node.children_by_type("function_declaration")
    for node in function_nodes:
        symbol = extract_typescript_function(node, file_path, repo_id)
        if symbol:
            symbols.append(symbol)
    
    # Query for class declarations
    class_nodes = root_node.children_by_type("class_declaration")
    for node in class_nodes:
        class_symbol = extract_typescript_class(node, file_path, repo_id)
        if class_symbol:
            symbols.append(class_symbol)
            
            # Extract methods within the class
            method_nodes = node.children_by_type("method_definition")
            for method_node in method_nodes:
                method_symbol = extract_typescript_method(method_node, file_path, repo_id, parent_id=class_symbol.id)
                if method_symbol:
                    symbols.append(method_symbol)
                    
                    # Create edge from class to method
                    edge = Edge(
                        source_id=class_symbol.id,
                        target_id=method_symbol.id,
                        type=EdgeType.CONTAINS,
                        repo_id=repo_id
                    )
                    edges.append(edge)
    
    return symbols, edges


def extract_typescript_function(
    node: Node, 
    file_path: str, 
    repo_id: str
) -> Optional[Symbol]:
    """
    Extract a function symbol from a TypeScript function declaration node.
    
    Args:
        node: Function declaration node
        file_path: Path to the file
        repo_id: Repository ID
        
    Returns:
        Symbol object or None if extraction failed
    """
    # This is a placeholder implementation
    # In a real implementation, we would extract TypeScript-specific function information
    try:
        # Get function name
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
            
        name = name_node.text.decode("utf8")
        
        # Create symbol
        symbol = Symbol(
            name=name,
            type=SymbolType.FUNCTION,
            file_path=file_path,
            language=Language.TYPESCRIPT,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            start_column=node.start_point[1] + 1,
            end_column=node.end_point[1] + 1,
            repo_id=repo_id
        )
        
        return symbol
    except Exception as e:
        logger.error(f"Error extracting TypeScript function: {e}")
        return None


def extract_typescript_class(
    node: Node, 
    file_path: str, 
    repo_id: str
) -> Optional[Symbol]:
    """
    Extract a class symbol from a TypeScript class declaration node.
    
    Args:
        node: Class declaration node
        file_path: Path to the file
        repo_id: Repository ID
        
    Returns:
        Symbol object or None if extraction failed
    """
    # This is a placeholder implementation
    # In a real implementation, we would extract TypeScript-specific class information
    try:
        # Get class name
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
            
        name = name_node.text.decode("utf8")
        
        # Create symbol
        symbol = Symbol(
            name=name,
            type=SymbolType.CLASS,
            file_path=file_path,
            language=Language.TYPESCRIPT,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            start_column=node.start_point[1] + 1,
            end_column=node.end_point[1] + 1,
            repo_id=repo_id
        )
        
        return symbol
    except Exception as e:
        logger.error(f"Error extracting TypeScript class: {e}")
        return None


def extract_typescript_method(
    node: Node, 
    file_path: str, 
    repo_id: str,
    parent_id: Optional[str] = None
) -> Optional[Symbol]:
    """
    Extract a method symbol from a TypeScript method definition node.
    
    Args:
        node: Method definition node
        file_path: Path to the file
        repo_id: Repository ID
        parent_id: ID of the parent symbol (e.g., class)
        
    Returns:
        Symbol object or None if extraction failed
    """
    # This is a placeholder implementation
    # In a real implementation, we would extract TypeScript-specific method information
    try:
        # Get method name
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
            
        name = name_node.text.decode("utf8")
        
        # Create symbol
        symbol = Symbol(
            name=name,
            type=SymbolType.METHOD,
            file_path=file_path,
            language=Language.TYPESCRIPT,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            start_column=node.start_point[1] + 1,
            end_column=node.end_point[1] + 1,
            parent_id=parent_id,
            repo_id=repo_id
        )
        
        return symbol
    except Exception as e:
        logger.error(f"Error extracting TypeScript method: {e}")
        return None
